'use client';

import { useState } from 'react';
import { SandpackProvider, SandpackLayout, SandpackPreview, SandpackCodeEditor } from '@codesandbox/sandpack-react';
import { githubLight, githubDark } from '@codesandbox/sandpack-themes';
import { useTheme } from 'next-themes';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Play, RotateCcw, Download, Maximize2 } from 'lucide-react';

interface ArtifactsCanvasProps {
  files: Record<string, string>;
  title: string;
  template?: 'react' | 'vanilla' | 'node' | 'vite-react';
  showPreview?: boolean;
  showEditor?: boolean;
}

export function ArtifactsCanvas({
  files,
  title,
  template = 'react',
  showPreview = true,
  showEditor = true
}: ArtifactsCanvasProps) {
  const { theme } = useTheme();
  const [isFullscreen, setIsFullscreen] = useState(false);

  const sandpackTheme = theme === 'dark' ? githubDark : githubLight;

  const handleRun = () => {
    // Trigger a refresh of the preview
    window.location.reload();
  };

  const handleReset = () => {
    // Reset to initial state
    window.location.reload();
  };

  const handleDownload = () => {
    // Create a zip download
    const element = document.createElement('a');
    const file = new Blob([JSON.stringify(files, null, 2)], { type: 'application/json' });
    element.href = URL.createObjectURL(file);
    element.download = `${title.toLowerCase().replace(/\s+/g, '-')}-artifact.json`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <Card className={`transition-all duration-200 ${isFullscreen ? 'fixed inset-4 z-50' : ''}`}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <CardTitle className="text-lg">{title}</CardTitle>
          <Badge variant="outline" className="text-xs">
            {template}
          </Badge>
          <Badge variant="secondary" className="text-xs">
            Live Preview
          </Badge>
        </div>
        <div className="flex items-center space-x-1">
          <Button variant="outline" size="sm" onClick={handleRun}>
            <Play className="h-3 w-3 mr-1" />
            Run
          </Button>
          <Button variant="outline" size="sm" onClick={handleReset}>
            <RotateCcw className="h-3 w-3 mr-1" />
            Reset
          </Button>
          <Button variant="outline" size="sm" onClick={handleDownload}>
            <Download className="h-3 w-3 mr-1" />
            Export
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsFullscreen(!isFullscreen)}
          >
            <Maximize2 className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <SandpackProvider
          files={files}
          template={template}
          theme={sandpackTheme}
          options={{
            externalResources: [
              'https://cdn.tailwindcss.com',
              'https://unpkg.com/react@18/umd/react.development.js',
              'https://unpkg.com/react-dom@18/umd/react-dom.development.js',
            ],
            visibleFiles: Object.keys(files),
            activeFile: Object.keys(files)[0],
            readOnly: false,
          }}
        >
          {showEditor && showPreview ? (
            <SandpackLayout className="h-96 rounded-b-lg overflow-hidden">
              <SandpackCodeEditor
                showTabs
                showLineNumbers
                wrapContent
                closableTabs
                className="h-full"
              />
              <SandpackPreview
                showNavigator={false}
                showOpenInCodeSandbox={false}
                className="h-full"
              />
            </SandpackLayout>
          ) : showEditor ? (
            <SandpackCodeEditor
              showTabs
              showLineNumbers
              wrapContent
              closableTabs
              className="h-96 rounded-b-lg"
            />
          ) : showPreview ? (
            <SandpackPreview
              showNavigator={false}
              showOpenInCodeSandbox={false}
              className="h-96 rounded-b-lg"
            />
          ) : null}
        </SandpackProvider>
      </CardContent>
    </Card>
  );
}

// Monaco Editor Wrapper for advanced editing
export function MonacoEditorWrapper({ files, onChange, language = 'javascript' }) {
  const [code, setCode] = useState(files['/App.js'] || '');

  const handleEditorChange = (value: string | undefined) => {
    const newCode = value || '';
    setCode(newCode);
    onChange?.(newCode);
  };

  return (
    <div className="h-full w-full">
      <SandpackProvider
        files={{
          '/App.js': code,
        }}
        template="react"
        options={{
          externalResources: ['https://cdn.tailwindcss.com'],
        }}
      >
        <SandpackCodeEditor
          showTabs={false}
          showLineNumbers={true}
          wrapContent={false}
          className="h-full"
        />
      </SandpackProvider>
    </div>
  );
}