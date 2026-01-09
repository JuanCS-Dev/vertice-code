'use server';

import { streamUI } from 'ai/rsc';
import { openai } from '@ai-sdk/openai';
import { z } from 'zod';
import { SalesChart } from '@/components/charts/sales-chart';
import { CodeEditor } from '@/components/artifacts/code-editor';
import { TaskList } from '@/components/ui/task-list';

export async function submitUserMessage(input: string) {
  'use server';

  const result = await streamUI({
    model: openai('gpt-4o'), // Will be replaced with our Vertex AI adapter
    system: 'You are Vertice-Code, an AI IDE assistant. You can generate UI components and code artifacts.',
    prompt: input,
    text: ({ content, done }) => {
      if (done) {
        return <div className="prose prose-sm max-w-none">{content}</div>;
      }
      return <div className="prose prose-sm max-w-none">{content}...</div>;
    },
    tools: {
      get_sales_data: {
        description: 'Generate a sales chart visualization',
        parameters: z.object({
          year: z.string().describe('Year for sales data'),
          metric: z.enum(['revenue', 'units', 'growth']).describe('Metric to visualize')
        }),
        generate: async function* ({ year, metric }) {
          yield <div className="flex items-center space-x-2 p-4 bg-muted rounded-lg">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <span>Loading {metric} data for {year}...</span>
          </div>;

          // Simulate data fetching
          await new Promise(resolve => setTimeout(resolve, 1000));

          const mockData = [
            { month: 'Jan', value: 45000 },
            { month: 'Feb', value: 52000 },
            { month: 'Mar', value: 48000 },
            { month: 'Apr', value: 61000 },
            { month: 'May', value: 55000 },
            { month: 'Jun', value: 67000 },
          ];

          return <SalesChart data={mockData} metric={metric} year={year} />;
        },
      },
      create_code_artifact: {
        description: 'Create an editable code artifact with live preview',
        parameters: z.object({
          title: z.string().describe('Title for the code artifact'),
          language: z.enum(['javascript', 'typescript', 'python', 'html', 'css']).describe('Programming language'),
          template: z.enum(['react', 'node', 'vanilla']).describe('Code template/framework')
        }),
        generate: async function* ({ title, language, template }) {
          yield <div className="flex items-center space-x-2 p-4 bg-muted rounded-lg">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <span>Creating {language} {template} artifact...</span>
          </div>;

          await new Promise(resolve => setTimeout(resolve, 500));

          // Generate initial code based on template
          const initialCode = generateInitialCode(language, template);

          return (
            <div className="border rounded-lg overflow-hidden">
              <div className="bg-card p-3 border-b">
                <h3 className="font-semibold">{title}</h3>
                <div className="flex items-center space-x-2 mt-1">
                  <span className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                    {language}
                  </span>
                  <span className="text-xs bg-secondary/10 text-secondary px-2 py-1 rounded">
                    {template}
                  </span>
                </div>
              </div>
              <CodeEditor
                initialCode={initialCode}
                language={language}
                title={title}
              />
            </div>
          );
        },
      },
      generate_task_list: {
        description: 'Generate an interactive task list for project planning',
        parameters: z.object({
          project: z.string().describe('Project name or description'),
          complexity: z.enum(['simple', 'medium', 'complex']).describe('Project complexity')
        }),
        generate: async function* ({ project, complexity }) {
          yield <div className="flex items-center space-x-2 p-4 bg-muted rounded-lg">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary"></div>
            <span>Planning tasks for {project}...</span>
          </div>;

          await new Promise(resolve => setTimeout(resolve, 800));

          // Generate tasks based on complexity
          const tasks = generateProjectTasks(project, complexity);

          return <TaskList tasks={tasks} project={project} />;
        },
      },
    },
  });

  return result.value;
}

function generateInitialCode(language: string, template: string): string {
  const templates = {
    javascript: {
      react: `import React, { useState } from 'react';

function App() {
  const [count, setCount] = useState(0);

  return (
    <div className="App">
      <h1>Hello from Vertice-Code!</h1>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}

export default App;`,
      node: `const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.json({ message: 'Hello from Vertice-Code API!' });
});

app.listen(3000, () => {
  console.log('Server running on port 3000');
});`,
      vanilla: `// Vertice-Code Generated JavaScript
document.addEventListener('DOMContentLoaded', () => {
  const app = document.getElementById('app');

  const heading = document.createElement('h1');
  heading.textContent = 'Hello from Vertice-Code!';
  app.appendChild(heading);

  const button = document.createElement('button');
  button.textContent = 'Click me!';
  button.onclick = () => alert('Hello!');
  app.appendChild(button);
});`
    },
    typescript: {
      react: `import React, { useState } from 'react';

interface AppProps {
  title?: string;
}

const App: React.FC<AppProps> = ({ title = 'Vertice-Code' }) => {
  const [count, setCount] = useState<number>(0);

  return (
    <div className="App">
      <h1>{title}</h1>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
};

export default App;`,
      node: `import express from 'express';
import { Request, Response } from 'express';

const app = express();
const port = 3000;

app.get('/', (req: Request, res: Response) => {
  res.json({ message: 'Hello from Vertice-Code TypeScript API!' });
});

app.listen(port, () => {
  console.log(\`Server running on port \${port}\`);
});`,
      vanilla: `// Vertice-Code Generated TypeScript
interface AppConfig {
  title: string;
  version: string;
}

const config: AppConfig = {
  title: 'Vertice-Code App',
  version: '1.0.0'
};

document.addEventListener('DOMContentLoaded', () => {
  const app = document.getElementById('app') as HTMLElement;

  const heading = document.createElement('h1');
  heading.textContent = config.title;
  app.appendChild(heading);

  const version = document.createElement('p');
  version.textContent = \`Version: \${config.version}\`;
  app.appendChild(version);
});`
    }
  };

  return templates.get(language, {}).get(template, '// Code template not available');
}

function generateProjectTasks(project: string, complexity: string): Array<{id: string, title: string, description: string, completed: boolean}> {
  const baseTasks = [
    {
      id: '1',
      title: 'Project Setup',
      description: 'Initialize project structure and dependencies',
      completed: false
    },
    {
      id: '2',
      title: 'Core Development',
      description: 'Implement main functionality',
      completed: false
    },
    {
      id: '3',
      title: 'Testing',
      description: 'Write and run tests',
      completed: false
    },
    {
      id: '4',
      title: 'Documentation',
      description: 'Create project documentation',
      completed: false
    }
  ];

  if (complexity === 'medium') {
    baseTasks.push({
      id: '5',
      title: 'UI/UX Design',
      description: 'Design user interface and experience',
      completed: false
    });
  } else if (complexity === 'complex') {
    baseTasks.push(
      {
        id: '5',
        title: 'UI/UX Design',
        description: 'Design user interface and experience',
        completed: false
      },
      {
        id: '6',
        title: 'Security Review',
        description: 'Conduct security assessment',
        completed: false
      },
      {
        id: '7',
        title: 'Performance Optimization',
        description: 'Optimize for performance and scalability',
        completed: false
      },
      {
        id: '8',
        title: 'Deployment Setup',
        description: 'Configure CI/CD and deployment',
        completed: false
      }
    );
  }

  return baseTasks;
}