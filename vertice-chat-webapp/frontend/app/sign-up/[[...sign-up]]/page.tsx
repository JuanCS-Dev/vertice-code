/**
 * Sign Up Page with Clerk
 *
 * Custom sign-up page with Vertice branding and Passkeys support
 *
 * Reference: https://clerk.com/docs/customization/sign-up
 */
import { SignUp } from '@clerk/nextjs';

export const dynamic = 'force-dynamic';

export default function SignUpPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground">Join Vertice</h1>
          <p className="text-muted-foreground mt-2">
            Create your account to start building with AI agents
          </p>
        </div>

        <SignUp
          appearance={{
            elements: {
              formButtonPrimary: 'bg-primary text-primary-foreground hover:bg-primary/90',
              card: 'bg-card border-border',
              headerTitle: 'text-foreground',
              headerSubtitle: 'text-muted-foreground',
              socialButtonsBlockButton: 'border-border hover:bg-accent',
              formFieldInput: 'border-border focus:border-ring',
              footerActionLink: 'text-primary hover:text-primary/90',
            },
          }}
          routing="path"
          path="/sign-up"
          signInUrl="/sign-in"
          redirectUrl="/onboarding"
        />
      </div>
    </div>
  );
}