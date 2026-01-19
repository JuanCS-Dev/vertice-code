import { ChatInterface } from '@/components/chat/chat-interface';
import { ProtectedRoute } from '@/components/auth/protected-route';

export const metadata = {
  title: 'Vertice Chat | Sovereign AI',
  description: 'AI-Native IDE with Generative UI and Artifacts',
};

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatInterface />
    </ProtectedRoute>
  );
}
