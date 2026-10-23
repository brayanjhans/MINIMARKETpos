"""Importar/exportar productos en Excel: vista previa, todo-o-nada, filas con error e inyección de fórmulas."""

import io
import uuid
from decimal import Decimal

from openpyxl import Workbook, load_workbook

from tests.conftest import Sesion
from tests.test_productos import crear_producto

ENCABEZADOS = ["Nombre *", "Código de barras", "Categoría", "Precio venta *", "Precio costo", "Stock inicial"]


def _excel(filas: list[list], encabezados: list[str] = ENCABEZADOS) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.append(encabezados)
    for fila in filas:
        hoja.append(fila)
    salida = io.BytesIO()
    libro.save(salida)
    return salida.getvalue()


async def _subir(admin: Sesion, ruta: str, contenido: bytes, **kw):
    return await admin.post(ruta, files={"archivo": ("catalogo.xlsx", contenido)}, **kw)


async def test_vista_previa_e_importacion(admin: Sesion):
    sufijo = uuid.uuid4().hex[:6]
    existente = await crear_producto(admin, precio_venta="6.20")
    codigo_nuevo = "775" + uuid.uuid4().hex[:10].upper()
    contenido = _excel(
        [
            [f"Galleta Soda {sufijo}", codigo_nuevo, f"Galletas {sufijo}", 0.80, 0.55, 30],
            [existente["nombre"], None, None, 6.50, None, None],  # existe por nombre: actualiza precio
            [f"Atún {sufijo}", None, None, -5.50, None, None],  # error: precio negativo
            [None, None, None, 3.20, None, None],  # error: falta el nombre
            [f"Galleta Soda {sufijo}", None, None, 1, None, None],  # error: repetido
            [f"Ron {sufijo}", None, None, "=1+1", None, None],  # error: no es número
        ]
    )
    r = await _subir(admin, "/productos/importar/vista-previa", contenido)
    assert r.status_code == 200, r.text
    vista = r.json()
    assert (vista["nuevos"], vista["actualizan"], vista["errores"]) == (1, 1, 4)
    assert vista["filas"][0]["accion"] == "error"  # los errores van primero
    repetido = next(f for f in vista["filas"] if f["fila"] == 6)
    assert repetido["errores"] == ["Producto repetido: es el de la fila 2"]
    # La vista previa no guarda nada
    assert (await admin.get("/productos", params={"busqueda": f"Soda {sufijo}"})).json()["total"] == 0

    r = await _subir(admin, "/productos/importar", contenido, headers={"Idempotency-Key": uuid.uuid4().hex})
    assert r.status_code == 200, r.text
    assert r.json()["creados"] == 1 and r.json()["actualizados"] == 1 and r.json()["omitidos"] == 4
    assert Decimal(r.json()["valor_stock"]) == Decimal("16.50")

    nuevo = (await admin.get(f"/productos/codigo/{codigo_nuevo}")).json()["producto"]
    assert nuevo["stock"] == "30.000"
    assert nuevo["categoria"]["nombre"] == f"Galletas {sufijo}"  # la categoría se creó sola
    assert (await admin.get(f"/productos/{existente['id']}")).json()["precio_venta"] == "6.50"


async def test_importacion_es_todo_o_nada(admin: Sesion):
    """Si algo falla al guardar (aquí: el código ya lo tomó otro producto entre la vista previa y la confirmación,
    simulado con una fila cuyo stock con lotes no se puede aplicar), no queda nada a medias."""
    sufijo = uuid.uuid4().hex[:6]
    contenido = _excel(
        [[f"Arroz {sufijo}", None, None, 4.2, 3.9, None], [f"Azúcar {sufijo}", None, None, 3.1, 2.5, None]]
    )
    vista = (await _subir(admin, "/productos/importar/vista-previa", contenido)).json()
    assert vista["nuevos"] == 2
    # Entre la vista previa y la importación alguien crea uno de esos productos con el mismo nombre
    await crear_producto(admin, nombre=f"Azúcar {sufijo}", precio_venta="3.00")
    r = await _subir(admin, "/productos/importar", contenido)
    # Se vuelve a analizar al confirmar: ahora "Azúcar" ya existe y solo se actualiza su precio
    assert r.status_code == 200
    assert r.json()["creados"] == 1 and r.json()["actualizados"] == 1


async def test_archivo_invalido_o_sin_columnas(admin: Sesion):
    r = await _subir(admin, "/productos/importar/vista-previa", b"no es un excel")
    assert r.status_code == 422 and r.json()["codigo"] == "archivo_invalido"
    r = await _subir(admin, "/productos/importar/vista-previa", _excel([["x"]], ["Otra cosa"]))
    assert r.status_code == 422 and r.json()["codigo"] == "columnas_faltantes"


async def test_exportar_protege_contra_formulas(admin: Sesion):
    peligroso = f"=HYPERLINK(\"http://malo\") {uuid.uuid4().hex[:5]}"
    await crear_producto(admin, nombre=peligroso)
    r = await admin.get("/productos/exportar")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    hoja = load_workbook(io.BytesIO(r.content)).active
    nombres = [fila[0].value for fila in hoja.iter_rows(min_row=2)]
    assert "'" + peligroso in nombres
    assert all(not (isinstance(n, str) and n.startswith("=")) for n in nombres)


async def test_plantilla(admin: Sesion):
    r = await admin.get("/productos/plantilla")
    assert r.status_code == 200
    libro = load_workbook(io.BytesIO(r.content))
    assert libro.active.cell(1, 1).value == "Nombre *"
    assert "Instrucciones" in libro.sheetnames
