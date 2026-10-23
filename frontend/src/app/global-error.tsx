"use client";

// Último recurso: si falla el layout raíz no hay estilos ni proveedores, así que todo va en línea.
export default function ErrorGlobal({ reset }: { error: Error; reset: () => void }) {
  return (
    <html lang="es">
      <body
        style={{
          margin: 0,
          minHeight: "100dvh",
          display: "grid",
          placeItems: "center",
          background: "#14213d",
          color: "#fff",
          fontFamily: "system-ui, sans-serif",
          padding: 20,
        }}
      >
        <div style={{ maxWidth: 420, textAlign: "center" }}>
          <h1 style={{ fontSize: 24, margin: "0 0 8px" }}>El sistema tuvo un problema</h1>
          <p style={{ color: "#aab4cf", lineHeight: 1.5, margin: "0 0 24px" }}>
            No se perdió ningún dato. Recarga la página; si el problema sigue, avisa al administrador.
          </p>
          <button
            type="button"
            onClick={reset}
            style={{
              background: "#ffc300",
              color: "#14213d",
              border: 0,
              borderRadius: 12,
              padding: "12px 22px",
              fontWeight: 800,
              fontSize: 15,
              cursor: "pointer",
            }}
          >
            Recargar
          </button>
        </div>
      </body>
    </html>
  );
}
