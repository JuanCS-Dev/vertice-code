/**
 * Sign In Page with Clerk
 *
 * Custom sign-in page with Vertice branding and Passkeys support
 *
 * Reference: https://clerk.com/docs/customization/sign-in
 */
import { SignIn } from '@clerk/nextjs';

export default function SignInPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-foreground">Welcome to Vertice</h1>
          <p className="text-muted-foreground mt-2">
            Sign in to start your agentic coding journey
          </p>
        </div>

        <SignIn
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
          path="/sign-in"
          signUpUrl="/sign-up"
          redirectUrl="/chat"
        />
      </div>
    </div>
  );
}