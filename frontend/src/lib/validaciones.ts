import { z } from "zod";

// Mismas reglas que el backend (app/schemas/usuarios.py)
export const esquemaPassword = z
  .string()
  .min(8, "Debe tener al menos 8 caracteres")
  .max(72, "Es demasiado larga")
  .regex(/[A-Za-z]/, "Debe contener letras")
  .regex(/\d/, "Debe contener números");

export const esquemaUsername = z
  .string()
  .trim()
  .toLowerCase()
  .regex(/^[a-z0-9._-]{3,50}$/, "Solo letras, números, punto, guion y guion bajo (3 a 50)");
