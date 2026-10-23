"""Catálogo de módulos, permisos y roles base del sistema."""

ROL_ADMINISTRADOR = "Administrador"
ROL_CAJERO = "Cajero"
ROL_ALMACENERO = "Almacenero"

# módulo -> {acción: descripción}. El código del permiso es "modulo.accion".
CATALOGO_PERMISOS: dict[str, dict[str, str]] = {
    "dashboard": {
        "ver": "Ver el dashboard",
    },
    "pos": {
        "vender": "Registrar ventas en el punto de venta",
        "aplicar_descuento": "Aplicar descuentos en ventas",
        "venta_credito": "Registrar ventas al fiado",
        "devolver": "Registrar devoluciones de productos",
        "anular_venta": "Anular ventas",
    },
    "caja": {
        "ver": "Ver su caja",
        "abrir": "Abrir caja",
        "cerrar": "Cerrar caja y hacer arqueo",
        "movimientos": "Registrar ingresos y egresos de caja",
        "ver_todas": "Ver cajas e historial de todos los cajeros",
    },
    "productos": {
        "ver": "Ver productos",
        "crear": "Crear productos",
        "editar": "Editar productos y precios",
        "eliminar": "Eliminar productos",
        "importar": "Importar productos desde Excel",
        "exportar": "Exportar productos a Excel",
    },
    "categorias": {
        "ver": "Ver categorías",
        "crear": "Crear categorías",
        "editar": "Editar categorías",
        "eliminar": "Eliminar categorías",
    },
    "marcas": {
        "ver": "Ver marcas",
        "crear": "Crear marcas",
        "editar": "Editar marcas",
        "eliminar": "Eliminar marcas",
    },
    "inventario": {
        "ver": "Ver stock y lotes",
        "kardex": "Ver kardex de productos",
        "ajustar": "Registrar ajustes y mermas",
        "aprobar_ajustes": "Aprobar ajustes de inventario",
        "inventario_fisico": "Realizar inventario físico",
        "transferir": "Enviar transferencias entre almacenes",
        "recibir_transferencia": "Recibir transferencias entre almacenes",
    },
    "sucursales": {
        "ver": "Ver sucursales y almacenes",
        "gestionar": "Crear y modificar sucursales, almacenes y cajas",
        "todas": "Ver información de todas las sucursales (no solo la actual)",
    },
    "proveedores": {
        "ver": "Ver proveedores",
        "crear": "Crear proveedores",
        "editar": "Editar proveedores",
        "eliminar": "Eliminar proveedores",
    },
    "compras": {
        "ver": "Ver compras y órdenes de compra",
        "crear": "Crear órdenes de compra",
        "recibir": "Recepcionar mercadería",
        "anular": "Anular compras",
        "pagar": "Registrar pagos a proveedores",
    },
    "clientes": {
        "ver": "Ver clientes",
        "crear": "Crear clientes",
        "editar": "Editar clientes",
        "eliminar": "Eliminar clientes",
        "cobrar": "Registrar abonos de cuentas por cobrar",
    },
    "reportes": {
        "ver": "Ver reportes",
        "ganancias": "Ver ganancias y costos",
        "exportar": "Exportar reportes a PDF y Excel",
    },
    "usuarios": {
        "ver": "Ver usuarios",
        "crear": "Crear usuarios",
        "editar": "Editar usuarios",
        "eliminar": "Desactivar usuarios",
    },
    "roles": {
        "ver": "Ver roles y permisos",
        "gestionar": "Crear y modificar roles y permisos",
    },
    "configuracion": {
        "ver": "Ver configuración",
        "editar": "Modificar configuración de la empresa",
    },
    "auditoria": {
        "ver": "Ver auditoría de acciones",
    },
}

ETIQUETAS_MODULOS: dict[str, str] = {
    "dashboard": "Dashboard",
    "pos": "Punto de venta",
    "caja": "Caja",
    "productos": "Productos",
    "categorias": "Categorías",
    "marcas": "Marcas",
    "inventario": "Inventario",
    "sucursales": "Sucursales y almacenes",
    "proveedores": "Proveedores",
    "compras": "Compras",
    "clientes": "Clientes",
    "reportes": "Reportes",
    "usuarios": "Usuarios",
    "roles": "Roles y permisos",
    "configuracion": "Configuración",
    "auditoria": "Auditoría",
}

TODOS_LOS_PERMISOS: list[str] = [f"{m}.{a}" for m, acciones in CATALOGO_PERMISOS.items() for a in acciones]

# El Administrador recibe siempre todos los permisos.
PERMISOS_POR_ROL: dict[str, list[str]] = {
    ROL_ADMINISTRADOR: TODOS_LOS_PERMISOS,
    ROL_CAJERO: [
        "dashboard.ver",
        "pos.vender",
        "pos.venta_credito",
        "caja.ver",
        "caja.abrir",
        "caja.cerrar",
        "caja.movimientos",
        "productos.ver",
        "categorias.ver",
        "marcas.ver",
        "inventario.ver",
        "inventario.recibir_transferencia",
        "clientes.ver",
        "clientes.crear",
        "clientes.cobrar",
    ],
    ROL_ALMACENERO: [
        "dashboard.ver",
        "productos.ver",
        "productos.crear",
        "productos.editar",
        "productos.importar",
        "productos.exportar",
        "categorias.ver",
        "categorias.crear",
        "categorias.editar",
        "marcas.ver",
        "marcas.crear",
        "marcas.editar",
        "inventario.ver",
        "inventario.kardex",
        "inventario.ajustar",
        "inventario.inventario_fisico",
        "inventario.transferir",
        "inventario.recibir_transferencia",
        "sucursales.ver",
        "proveedores.ver",
        "proveedores.crear",
        "proveedores.editar",
        "compras.ver",
        "compras.crear",
        "compras.recibir",
    ],
}

SUCURSAL_PRINCIPAL = {"codigo": "0000", "nombre": "Principal", "direccion": "Av. Principal 123, Lima"}

# Numeración de documentos internos: clave -> (prefijo, descripción)
CORRELATIVOS: dict[str, tuple[str, str]] = {
    "ORDEN_COMPRA": ("OC", "Órdenes de compra"),
    "AJUSTE": ("AJ", "Ajustes de inventario"),
    "TRANSFERENCIA": ("TR", "Transferencias entre almacenes"),
    "DEVOLUCION": ("DV", "Devoluciones de ventas"),
    "INVENTARIO_FISICO": ("IF", "Inventarios físicos"),
}

# Motivos de ajuste: (nombre, tipo, es_merma)
MOTIVOS_AJUSTE: list[tuple[str, str, bool]] = [
    ("Producto vencido", "SALIDA", True),
    ("Producto dañado o roto", "SALIDA", True),
    ("Robo o pérdida", "SALIDA", True),
    ("Consumo interno", "SALIDA", False),
    ("Sobrante encontrado", "ENTRADA", False),
    ("Bonificación del proveedor", "ENTRADA", False),
    ("Corrección de error de registro", "AMBOS", False),
]

# Parámetros del sistema: clave -> (valor, tipo, módulo, descripción)
PARAMETROS_SISTEMA: dict[str, tuple[object, str, str, str]] = {
    "ventas.permitir_sin_stock": (False, "BOOLEANO", "ventas", "Permitir vender productos sin stock suficiente"),
    "ventas.redondeo_efectivo": (
        "0.00", "DECIMAL", "ventas", "Redondeo del total en efectivo (0.00 = sin redondeo, 0.10 = a 10 céntimos)",
    ),
    "ventas.descuento_maximo_cajero": (
        "10", "DECIMAL", "ventas", "Descuento máximo (%) que puede aplicar un cajero sin autorización",
    ),
    "ventas.cliente_obligatorio_desde": (
        "700.00", "DECIMAL", "ventas", "Monto desde el cual la boleta exige identificar al cliente (DNI)",
    ),
    "inventario.dias_alerta_vencimiento": (
        30, "ENTERO", "inventario", "Días de anticipación para alertar productos por vencer",
    ),
    "inventario.ajustes_requieren_aprobacion": (
        False, "BOOLEANO", "inventario", "Los ajustes de inventario deben ser aprobados antes de aplicarse",
    ),
    "inventario.metodo_salida_lotes": ("FEFO", "TEXTO", "inventario", "Salida de lotes: FEFO (primero en vencer)"),
    "clientes.dias_credito_defecto": (30, "ENTERO", "clientes", "Días de plazo por defecto para ventas al fiado"),
    "seguridad.max_intentos_login": (5, "ENTERO", "seguridad", "Intentos fallidos antes de bloquear el usuario"),
    "seguridad.minutos_bloqueo": (15, "ENTERO", "seguridad", "Minutos de bloqueo tras superar los intentos"),
    "seguridad.max_intentos_ip": (
        20, "ENTERO", "seguridad", "Ingresos fallidos permitidos desde un mismo equipo (IP) dentro de la ventana",
    ),
    "seguridad.minutos_ventana_ip": (
        15, "ENTERO", "seguridad", "Minutos que se cuentan los ingresos fallidos de un mismo equipo (IP)",
    ),
    "caja.denominaciones": (
        ["200", "100", "50", "20", "10", "5", "2", "1", "0.50", "0.20", "0.10"],
        "JSON",
        "caja",
        "Billetes y monedas usados en el arqueo",
    ),
}

DESCRIPCION_ROLES: dict[str, str] = {
    ROL_ADMINISTRADOR: "Acceso total al sistema",
    ROL_CAJERO: "Ventas, caja y atención de clientes",
    ROL_ALMACENERO: "Productos, inventario, proveedores y compras",
}
