"""Productos: códigos únicos, presentaciones, edición concurrente, búsqueda y fotos."""

import io
import uuid

from PIL import Image

from tests.conftest import Sesion


def _codigo() -> str:
    return "77" + uuid.uuid4().hex[:11].upper()


def _nombre(base: str = "Producto") -> str:
    return f"{base} {uuid.uuid4().hex[:6]}"


async def crear_producto(admin: Sesion, **extra) -> dict:
    datos = {"nombre": _nombre(), "precio_venta": "5.50", "precio_costo": "3.20", "codigos": [_codigo()], **extra}
    r = await admin.post("/productos", json=datos)
    assert r.status_code == 201, r.text
    return r.json()


async def test_crear_y_buscar_por_codigo(admin: Sesion):
    codigo = _codigo()
    p = await crear_producto(admin, codigos=[codigo], stock_minimo="10")
    assert p["codigo_barras"] == codigo
    assert p["margen"] == "41.8"  # (5.50 - 3.20) / 5.50
    assert p["estado_stock"] == "sin_stock"

    r = await admin.get(f"/productos/codigo/{codigo.lower()}")
    assert r.status_code == 200
    assert r.json()["producto"]["id"] == p["id"]
    assert r.json()["presentacion"] is None

    r = await admin.get("/productos/codigo/000000000")
    assert r.status_code == 404


async def test_codigo_unico_entre_productos_y_presentaciones(admin: Sesion):
    codigo = _codigo()
    await crear_producto(admin, codigos=[codigo])
    r = await admin.post("/productos", json={"nombre": _nombre(), "precio_venta": "1", "codigos": [codigo]})
    assert r.status_code == 409
    assert r.json()["codigo"] == "codigo_duplicado"

    # El mismo código en la presentación de OTRO producto también se rechaza
    r = await admin.post(
        "/productos",
        json={
            "nombre": _nombre(),
            "precio_venta": "1",
            "presentaciones": [{"nombre": "Six pack", "factor": "6", "precio_venta": "5", "codigos": [codigo]}],
        },
    )
    assert r.status_code == 409

    # Y dentro del mismo producto
    otro = _codigo()
    r = await admin.post(
        "/productos",
        json={
            "nombre": _nombre(),
            "precio_venta": "1",
            "codigos": [otro],
            "presentaciones": [{"nombre": "Caja", "factor": "12", "precio_venta": "10", "codigos": [otro]}],
        },
    )
    assert r.status_code == 422


async def test_presentacion_por_codigo(admin: Sesion):
    codigo_six = _codigo()
    p = await crear_producto(
        admin, presentaciones=[{"nombre": "Six pack", "factor": "6", "precio_venta": "30", "codigos": [codigo_six]}]
    )
    r = await admin.get(f"/productos/codigo/{codigo_six}")
    assert r.json()["presentacion"]["nombre"] == "Six pack"
    assert r.json()["presentacion"]["factor"] == "6.000"
    assert p["presentaciones"][0]["codigos"] == [codigo_six]


async def test_edicion_concurrente_avisa(admin: Sesion):
    p = await crear_producto(admin)
    r1 = await admin.patch(f"/productos/{p['id']}", json={"version": p["version"], "precio_venta": "6.00"})
    assert r1.status_code == 200
    assert r1.json()["version"] == p["version"] + 1
    # Otra persona guarda con la versión vieja que tenía en pantalla
    r2 = await admin.patch(f"/productos/{p['id']}", json={"version": p["version"], "precio_venta": "7.00"})
    assert r2.status_code == 409
    assert r2.json()["codigo"] == "version_desactualizada"

    historial = (await admin.get(f"/productos/{p['id']}/historial-precios")).json()
    assert historial[0]["tipo"] == "VENTA"
    assert historial[0]["precio_anterior"].startswith("5.5")


async def test_editar_codigos_y_presentaciones(admin: Sesion):
    p = await crear_producto(
        admin, presentaciones=[{"nombre": "Caja x12", "factor": "12", "precio_venta": "60", "codigos": [_codigo()]}]
    )
    nuevo_base = _codigo()
    pres = p["presentaciones"][0]
    r = await admin.patch(
        f"/productos/{p['id']}",
        json={
            "version": p["version"],
            "codigos": [nuevo_base],
            "presentaciones": [{**{k: pres[k] for k in ("id", "nombre", "factor")}, "precio_venta": "58",
                                "codigos": []}],
        },
    )
    assert r.status_code == 200, r.text
    assert r.json()["codigos"] == [nuevo_base]
    assert r.json()["presentaciones"][0]["codigos"] == []
    assert r.json()["presentaciones"][0]["precio_venta"] == "58.00"
    # El código viejo quedó libre: otro producto lo puede usar
    await crear_producto(admin, codigos=[p["codigos"][0]])


async def test_busqueda_por_palabras_en_cualquier_orden(admin: Sesion):
    marca = uuid.uuid4().hex[:5]
    await crear_producto(admin, nombre=f"Gaseosa Inca Kola {marca} 1.5 L")
    r = await admin.get("/productos", params={"busqueda": f"kola {marca}"})
    assert r.json()["total"] == 1
    r = await admin.get("/productos", params={"busqueda": f"KÓLA {marca} inca"})  # sin importar tildes/mayúsculas
    assert r.json()["total"] == 1


async def test_nombre_duplicado(admin: Sesion):
    p = await crear_producto(admin)
    r = await admin.post("/productos", json={"nombre": p["nombre"], "precio_venta": "1"})
    assert r.status_code == 409


async def test_decimales_solo_si_el_producto_los_admite(admin: Sesion):
    r = await admin.post("/productos", json={"nombre": _nombre(), "precio_venta": "1", "stock_minimo": "2.5"})
    assert r.status_code == 422
    r = await admin.post(
        "/productos",
        json={"nombre": _nombre(), "precio_venta": "4.20", "unidad_medida": "KILOGRAMO", "permite_decimales": True,
              "stock_minimo": "2.5"},
    )
    assert r.status_code == 201


async def test_cajero_no_ve_costos(admin: Sesion, cliente, crear_usuario):
    p = await crear_producto(admin)
    usuario, clave = await crear_usuario("Cajero")
    from tests.conftest import iniciar_sesion

    cajero = Sesion(cliente, await iniciar_sesion(cliente, usuario["username"], clave))
    r = await cajero.get(f"/productos/{p['id']}")
    assert r.status_code == 200
    assert r.json()["precio_costo"] is None
    assert r.json()["margen"] is None
    r = await cajero.patch(f"/productos/{p['id']}", json={"version": 1, "precio_venta": "1"})
    assert r.status_code == 403


async def test_eliminar_producto_sin_movimientos(admin: Sesion):
    p = await crear_producto(admin)
    r = await admin.delete(f"/productos/{p['id']}")
    assert r.status_code == 200
    assert (await admin.get(f"/productos/{p['id']}")).status_code == 404


def _foto_jpeg(ancho: int = 3000, alto: int = 2000) -> bytes:
    imagen = Image.new("RGB", (ancho, alto), (200, 30, 30))
    exif = Image.Exif()
    exif[0x0112] = 6  # orientación: rotada 90°
    exif[0x8825] = {2: (12.0, 3.0, 4.0)}  # datos GPS
    salida = io.BytesIO()
    imagen.save(salida, "JPEG", quality=95, exif=exif)
    return salida.getvalue()


async def test_foto_se_convierte_a_webp_liviano(admin: Sesion):
    p = await crear_producto(admin)
    r = await admin.cliente.put(
        f"/api/v1/productos/{p['id']}/imagen",
        headers=admin.headers,
        files={"archivo": ("foto.jpg", _foto_jpeg(), "image/jpeg")},
    )
    assert r.status_code == 200, r.text
    url, mini = r.json()["imagen_url"], r.json()["miniatura_url"]

    grande = await admin.cliente.get(url)
    assert grande.status_code == 200
    assert grande.headers["content-type"] == "image/webp"
    assert "immutable" in grande.headers["cache-control"]
    imagen = Image.open(io.BytesIO(grande.content))
    assert imagen.format == "WEBP"
    ancho, alto = imagen.size
    assert alto == 800 and ancho < alto  # se aplicó la rotación EXIF (vertical) y se redujo a 800 px
    assert not imagen.getexif()  # sin metadatos (ni GPS)
    assert len(grande.content) < 60_000

    miniatura = Image.open(io.BytesIO((await admin.cliente.get(mini)).content))
    assert max(miniatura.size) == 160

    # Al reemplazarla, la anterior se borra
    r = await admin.cliente.put(
        f"/api/v1/productos/{p['id']}/imagen",
        headers=admin.headers,
        files={"archivo": ("foto.png", _png(), "image/png")},
    )
    assert r.status_code == 200
    assert (await admin.cliente.get(url)).status_code == 404


def _png() -> bytes:
    salida = io.BytesIO()
    Image.new("RGBA", (300, 300), (0, 0, 255, 128)).save(salida, "PNG")
    return salida.getvalue()


async def test_archivo_que_no_es_imagen(admin: Sesion):
    p = await crear_producto(admin)
    r = await admin.cliente.put(
        f"/api/v1/productos/{p['id']}/imagen",
        headers=admin.headers,
        files={"archivo": ("foto.jpg", b"esto no es una imagen", "image/jpeg")},
    )
    assert r.status_code == 422
    assert r.json()["codigo"] == "imagen_invalida"


async def test_ruta_de_media_no_permite_salir_de_la_carpeta(admin: Sesion):
    r = await admin.cliente.get("/api/v1/media/productos/..%2F..%2F.env")
    assert r.status_code == 404


async def test_categorias_y_marcas(admin: Sesion):
    nombre = f"Categoría {uuid.uuid4().hex[:5]}"
    r = await admin.post("/categorias", json={"nombre": nombre, "color": "#FFAA00"})
    assert r.status_code == 201
    categoria = r.json()
    assert categoria["color"] == "#ffaa00"
    assert (await admin.post("/categorias", json={"nombre": nombre})).status_code == 409

    await crear_producto(admin, categoria_id=categoria["id"])
    r = await admin.delete(f"/categorias/{categoria['id']}")
    assert r.status_code == 409  # tiene productos
    lista = (await admin.get("/categorias")).json()
    assert next(c for c in lista if c["id"] == categoria["id"])["productos"] == 1

    marca = (await admin.post("/marcas", json={"nombre": f"Marca {uuid.uuid4().hex[:5]}"})).json()
    r = await admin.delete(f"/marcas/{marca['id']}")
    assert r.status_code == 200
