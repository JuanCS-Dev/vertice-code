// src/components/auth/SignIn.tsx
import { SignIn } from "@clerk/clerk-react";
import React from "react";

/**
 * Componente de Login principal.
 * Força o uso de Passkeys/Passwordless conforme Diretriz de Segurança 2026.
 * 
 * @returns {React.JSX.Element} O componente de formulário de login.
 */
export default function SignInPage(): React.JSX.Element {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md space-y-8">
        <SignIn 
          path="/sign-in"
          routing="path"
          signUpUrl="/sign-up"
          appearance={{
            elements: {
              footerAction: { display: "none" }, // Remove opção de senha (Legacy)
              card: "shadow-xl border border-gray-200 dark:border-gray-800",
            },
            variables: {
              colorPrimary: "#0F172A", // Brand color
            }
          }}
        />
      </div>
    </div>
  );
}
