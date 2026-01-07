// vertice-chat-webapp/frontend/components/github/repo-browser.tsx

'use client';

import { useState, useEffect } from 'react';
import { GitHubClient, GitHubRepo, GitHubFile } from '@/lib/github/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import { Search, Star, GitFork, ExternalLink, Folder, File, Download } from 'lucide-react';
import { cn } from '@/lib/utils';

interface RepoBrowserProps {
  onFileSelect?: (file: GitHubFile) => void;
  onRepoSelect?: (repo: GitHubRepo) => void;
}

export function RepoBrowser({ onFileSelect, onRepoSelect }: RepoBrowserProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [repos, setRepos] = useState<GitHubRepo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<GitHubRepo | null>(null);
  const [repoContents, setRepoContents] = useState<GitHubFile[]>([]);
  const [currentPath, setCurrentPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);

  const client = new GitHubClient();

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const results = await client.searchRepos(searchQuery);
      setRepos(results.items.slice(0, 10));
      setSelectedRepo(null);
      setRepoContents([]);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setSearching(false);
    }
  };

  const handleRepoSelect = async (repo: GitHubRepo) => {
    setSelectedRepo(repo);
    setLoading(true);

    try {
      const contents = await client.getRepoContents(repo.owner.login, repo.name);
      setRepoContents(contents);
      setCurrentPath('');
      onRepoSelect?.(repo);
    } catch (error) {
      console.error('Failed to load repo contents:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = async (file: GitHubFile) => {
    if (file.type === 'dir' && selectedRepo) {
      setLoading(true);
      try {
        const contents = await client.getRepoContents(
          selectedRepo.owner.login,
          selectedRepo.name,
          file.path
        );
        setRepoContents(contents);
        setCurrentPath(file.path);
      } catch (error) {
        console.error('Failed to load directory:', error);
      } finally {
        setLoading(false);
      }
    } else if (file.type === 'file') {
      onFileSelect?.(file);
    }
  };

  const handleBack = async () => {
    if (!selectedRepo || !currentPath) {
      setSelectedRepo(null);
      setRepoContents([]);
      return;
    }

    const pathParts = currentPath.split('/').filter(Boolean);
    pathParts.pop();
    const newPath = pathParts.join('/');

    setLoading(true);
    try {
      const contents = await client.getRepoContents(
        selectedRepo.owner.login,
        selectedRepo.name,
        newPath
      );
      setRepoContents(contents);
      setCurrentPath(newPath);
    } catch (error) {
      console.error('Failed to go back:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search Header */}
      <div className="p-4 border-b border-border">
        <div className="flex gap-2">
          <Input
            placeholder="Search GitHub repositories..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1"
          />
          <Button onClick={handleSearch} disabled={searching}>
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
        </div>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {/* Repository List */}
          {!selectedRepo && repos.length > 0 && (
            <div className="space-y-3">
              <h3 className="text-lg font-semibold">Search Results</h3>
              {repos.map((repo) => (
                <Card key={repo.id} className="cursor-pointer hover:bg-accent/50 transition-colors">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-base hover:text-primary">
                          {repo.full_name}
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {repo.description || 'No description available'}
                        </CardDescription>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          window.open(repo.html_url, '_blank');
                        }}
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      {repo.language && (
                        <Badge variant="secondary">{repo.language}</Badge>
                      )}
                      <div className="flex items-center gap-1">
                        <Star className="h-3 w-3" />
                        {repo.stargazers_count.toLocaleString()}
                      </div>
                      <div className="flex items-center gap-1">
                        <GitFork className="h-3 w-3" />
                        {repo.forks_count.toLocaleString()}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Repository Contents */}
          {selectedRepo && (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleBack}
                  disabled={loading}
                >
                  ← Back
                </Button>
                <h3 className="text-lg font-semibold">{selectedRepo.full_name}</h3>
                {currentPath && (
                  <span className="text-muted-foreground">/ {currentPath}</span>
                )}
              </div>

              {loading ? (
                <div className="space-y-2">
                  {[...Array(5)].map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : (
                <div className="space-y-1">
                  {repoContents.map((item) => (
                    <div
                      key={item.path}
                      className={cn(
                        "flex items-center gap-3 p-2 rounded-md hover:bg-accent/50 cursor-pointer transition-colors",
                        item.type === 'dir' && "font-medium"
                      )}
                      onClick={() => handleFileClick(item)}
                    >
                      {item.type === 'dir' ? (
                        <Folder className="h-4 w-4 text-blue-500" />
                      ) : (
                        <File className="h-4 w-4 text-gray-500" />
                      )}
                      <span className="flex-1">{item.name}</span>
                      {item.type === 'file' && item.size > 0 && (
                        <span className="text-sm text-muted-foreground">
                          {(item.size / 1024).toFixed(1)} KB
                        </span>
                      )}
                      {item.type === 'file' && item.download_url && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(item.download_url!, '_blank');
                          }}
                        >
                          <Download className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Empty States */}
          {!searching && repos.length === 0 && searchQuery && (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No repositories found for "{searchQuery}"</p>
              <p className="text-sm">Try a different search term</p>
            </div>
          )}

          {!searchQuery && !selectedRepo && (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Search for GitHub repositories</p>
              <p className="text-sm">Use the search bar above to find repositories</p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}