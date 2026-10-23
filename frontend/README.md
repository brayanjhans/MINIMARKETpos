# Frontend – Minimarket POS (Next.js 16)

> Documentación completa en la Fase 7.

```powershell
cd frontend
npm install
npm run dev        # http://localhost:3010  (requiere el backend en http://localhost:8010)
```

- El navegador llama a `/api/v1/...` en el mismo origen y Next lo reenvía al backend (`BACKEND_URL`).
  Así la cookie de sesión (httpOnly) es de primer nivel y no hace falta CORS.
- `src/proxy.ts` redirige a `/login` si no hay sesión (en Next 16 reemplaza a `middleware.ts`).
- Componentes de interfaz: shadcn/ui en `src/components/ui`.
