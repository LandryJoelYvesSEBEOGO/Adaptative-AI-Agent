import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Send,
  Bot,
  User,
  Loader2,
  ThumbsUp,
  ThumbsDown,
  Copy,
  RotateCcw,
  Menu,
  LogOut,
  Settings,
  MessageSquare,
  Plus,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { useAuthStore } from "@/stores/authStore";
import { useToast } from "@/hooks/use-toast";
import ThemeToggle from "@/components/ThemeToggle";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  citations?: { id: number; source: string; excerpt: string }[];
}

interface SuggestedQuestion {
  text: string;
}

// Mock responses for demo
const mockResponses = [
  {
    content: `D'après notre documentation, voici les étapes pour configurer les paramètres de sécurité [1]:

1. Accédez au panneau d'administration
2. Naviguez vers "Paramètres > Sécurité"
3. Activez l'authentification à deux facteurs [2]
4. Configurez les règles de pare-feu selon vos besoins

Pour plus de détails, consultez également notre guide sur les bonnes pratiques [3].`,
    citations: [
      { id: 1, source: "Guide de sécurité v2.0", excerpt: "Les paramètres de sécurité sont accessibles depuis le panneau d'administration..." },
      { id: 2, source: "FAQ Authentification", excerpt: "L'authentification à deux facteurs (2FA) ajoute une couche de sécurité supplémentaire..." },
      { id: 3, source: "Bonnes pratiques IT", excerpt: "Pour garantir la sécurité de votre système, nous recommandons les mesures suivantes..." },
    ],
  },
  {
    content: `Les meilleures pratiques pour l'intégration API incluent [1]:

- Utiliser des tokens d'authentification JWT
- Implémenter le rate limiting pour protéger vos endpoints
- Valider toutes les entrées utilisateur [2]
- Utiliser HTTPS pour toutes les communications

Notre SDK simplifie grandement ces étapes [3].`,
    citations: [
      { id: 1, source: "Documentation API v3.1", excerpt: "Les bonnes pratiques d'intégration API garantissent la sécurité et la fiabilité..." },
      { id: 2, source: "Guide de validation", excerpt: "La validation des entrées est essentielle pour prévenir les injections..." },
      { id: 3, source: "SDK Guide", excerpt: "Notre SDK fournit des méthodes prêtes à l'emploi pour l'authentification..." },
    ],
  },
];

const suggestedQuestions: SuggestedQuestion[] = [
  { text: "Comment configurer l'authentification ?" },
  { text: "Quelles sont les limites de l'API ?" },
  { text: "Comment optimiser les performances ?" },
];

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    // Simulate API call with streaming effect
    await new Promise((resolve) => setTimeout(resolve, 1500));

    const mockResponse = mockResponses[Math.floor(Math.random() * mockResponses.length)];
    
    const assistantMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: mockResponse.content,
      timestamp: new Date(),
      citations: mockResponse.citations,
    };

    setMessages((prev) => [...prev, assistantMessage]);
    setIsLoading(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleSuggestionClick = (question: string) => {
    setInput(question);
    textareaRef.current?.focus();
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    toast({
      title: "Copié",
      description: "Le texte a été copié dans le presse-papiers",
    });
  };

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  const renderCitation = (text: string, citations?: Message["citations"]) => {
    if (!citations) return text;

    const parts = text.split(/(\[\d+\])/g);
    return parts.map((part, index) => {
      const match = part.match(/\[(\d+)\]/);
      if (match) {
        const citationId = parseInt(match[1]);
        const citation = citations.find((c) => c.id === citationId);
        if (citation) {
          return (
            <button
              key={index}
              className="text-primary hover:underline font-medium mx-0.5"
              onClick={() =>
                toast({
                  title: citation.source,
                  description: citation.excerpt,
                })
              }
            >
              [{citationId}]
            </button>
          );
        }
      }
      return <span key={index}>{part}</span>;
    });
  };

  return (
    <div className="min-h-screen bg-background flex relative">
      {/* Background effects inspired by template */}
      <div className="absolute inset-0 pointer-events-none opacity-40 dark:opacity-20">
        <div 
          className="absolute inset-0 mix-blend-overlay"
          style={{
            backgroundImage: "url('https://grainy-gradients.vercel.app/noise.svg')",
          }}
        />
      </div>
      <div className="absolute top-0 right-0 w-[40rem] h-[40rem] bg-gradient-to-b from-primary/10 to-transparent opacity-50 dark:opacity-30 blur-3xl pointer-events-none rounded-full translate-x-1/4 -translate-y-1/4" />
      
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-background/80 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed lg:static inset-y-0 left-0 z-50 w-72 bg-sidebar border-r border-sidebar-border flex flex-col transition-transform duration-300 lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Sidebar Header */}
        <div className="flex items-center justify-between p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-foreground flex items-center justify-center">
              <Bot className="w-5 h-5 text-background" />
            </div>
            <div className="flex flex-col">
              <span className="font-oswald text-lg font-medium tracking-tight">
                RAG<span className="text-primary">SYSTEM</span>
              </span>
              <span className="text-[0.6rem] font-space uppercase tracking-widest text-muted-foreground">
                RAG Assistant
              </span>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <Button onClick={handleNewChat} className="w-full" variant="outline">
            <Plus className="w-4 h-4 mr-2" />
            Nouvelle conversation
          </Button>
        </div>

        {/* Chat History */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          <p className="text-xs font-space uppercase tracking-widest text-muted-foreground mb-3">
            Historique
          </p>
          {[1, 2, 3].map((i) => (
            <button
              key={i}
              className="w-full text-left p-3 rounded-lg hover:bg-sidebar-accent transition-colors group"
            >
              <div className="flex items-center gap-3">
                <MessageSquare className="w-4 h-4 text-muted-foreground group-hover:text-foreground" />
                <span className="text-sm truncate">Conversation {i}</span>
              </div>
            </button>
          ))}
        </div>

        {/* User section */}
        <div className="p-4 border-t border-sidebar-border">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center">
              <span className="text-sm font-medium text-primary">
                {user?.name.charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" className="flex-1">
              <Settings className="w-4 h-4 mr-2" />
              Paramètres
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleLogout}
              className="text-muted-foreground hover:text-destructive"
            >
              <LogOut className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Mobile Header */}
        <header className="lg:hidden flex items-center justify-between gap-4 p-4 border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(true)}>
              <Menu className="w-5 h-5" />
            </Button>
            <div className="flex items-center gap-2">
              <Bot className="w-5 h-5 text-primary" />
              <span className="font-oswald font-medium">RAG Chat</span>
            </div>
          </div>
          <ThemeToggle variant="compact" />
        </header>
        
        {/* Desktop Header */}
        <header className="hidden lg:flex items-center justify-between px-6 py-4 border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-primary" />
            <span className="font-oswald font-medium">RAG Chat</span>
          </div>
          <ThemeToggle variant="compact" />
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto relative">
          {/* Background effects for messages area */}
          <div className="absolute inset-0 pointer-events-none opacity-30 dark:opacity-10">
            <div 
              className="absolute inset-0"
              style={{
                backgroundImage: "url('https://grainy-gradients.vercel.app/noise.svg')",
              }}
            />
          </div>
          <div className="max-w-3xl mx-auto p-4 lg:p-8 space-y-6 relative z-10">
            {messages.length === 0 ? (
              <div className="text-center py-16">
                <div className="relative inline-block mb-6">
                  <div className="absolute inset-0 bg-primary/20 rounded-2xl blur-xl" />
                  <div className="relative w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center">
                    <Bot className="w-8 h-8 text-primary" />
                  </div>
                </div>
                <h2 className="text-3xl font-oswald font-medium mb-3">
                  Comment puis-je vous aider ?
                </h2>
                <p className="text-muted-foreground mb-8 text-lg">
                  Posez une question sur notre documentation ou nos produits
                </p>
                <div className="flex flex-wrap justify-center gap-3">
                  {suggestedQuestions.map((q, i) => (
                    <Button
                      key={i}
                      variant="outline"
                      onClick={() => handleSuggestionClick(q.text)}
                      className="text-sm hover:border-primary/50 hover:bg-primary/5 transition-all"
                    >
                      {q.text}
                    </Button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-4",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === "assistant" && (
                    <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "chat-bubble relative group",
                      message.role === "user"
                        ? "chat-bubble-user"
                        : "chat-bubble-assistant"
                    )}
                  >
                    {/* Subtle gradient effect for assistant messages */}
                    {message.role === "assistant" && (
                      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
                    )}
                    <div className="whitespace-pre-wrap">
                      {message.role === "assistant"
                        ? renderCitation(message.content, message.citations)
                        : message.content}
                    </div>
                    {message.role === "assistant" && (
                      <div className="flex items-center gap-2 mt-4 pt-3 border-t border-border/50">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-2 text-muted-foreground hover:text-foreground"
                          onClick={() => handleCopy(message.content)}
                        >
                          <Copy className="w-3.5 h-3.5 mr-1.5" />
                          Copier
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-2 text-muted-foreground hover:text-success"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 px-2 text-muted-foreground hover:text-destructive"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                        </Button>
                      </div>
                    )}
                  </div>
                  {message.role === "user" && (
                    <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-primary-foreground" />
                    </div>
                  )}
                </div>
              ))
            )}
            {isLoading && (
              <div className="flex gap-4">
                <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-primary" />
                </div>
                <Card className="p-4">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">L'assistant écrit...</span>
                  </div>
                </Card>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area with enhanced styling */}
        <div className="border-t border-border bg-background/80 backdrop-blur-xl sticky bottom-0 z-10">
          <div className="max-w-3xl mx-auto p-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-t from-background to-transparent pointer-events-none" />
              <Textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Posez votre question..."
                className="min-h-[60px] max-h-[200px] pr-14 resize-none bg-card border-border/50 focus:border-primary/50 transition-colors"
                rows={2}
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                size="icon"
                className="absolute right-2 bottom-2 shadow-lg hover:shadow-xl transition-shadow"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground text-center mt-3">
              RAG System peut faire des erreurs. Vérifiez les informations importantes.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
