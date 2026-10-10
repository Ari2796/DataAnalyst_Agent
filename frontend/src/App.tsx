import React, { useEffect, useState } from 'react';
import { Navbar } from './components/Navbar';
import { FileUpload } from './components/FileUpload';
import { DatasetSidebar } from './components/DatasetSidebar';
import { ChatInterface } from './components/ChatInterface';
import { SchemaMappingModal } from './components/SchemaMappingModal';
import { DataPreviewModal } from './components/DataPreviewModal';
import type { DatasetProfile } from './types';
import { api } from './services/api';

export const App: React.FC = () => {
  const [profile, setProfile] = useState<DatasetProfile | null>(null);
  const [llmConfigured, setLlmConfigured] = useState<boolean>(false);
  const [activeQuery, setActiveQuery] = useState<string | null>(null);
  const [isMappingsModalOpen, setIsMappingsModalOpen] = useState(false);
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'chat' | 'dataset'>('chat');

  useEffect(() => {
    // Check backend health & LLM state
    api.checkHealth()
      .then((data) => {
        setLlmConfigured(data.llm_configured);
      })
      .catch((err) => {
        console.warn('Backend not reachable on initial check:', err);
      });
  }, []);

  const handleUploadSuccess = (newProfile: DatasetProfile) => {
    setProfile(newProfile);
    setActiveTab('chat');
  };

  const handleResetSession = async () => {
    if (profile) {
      try {
        await api.deleteSession(profile.dataset_id);
      } catch (e) {
        console.warn('Session cleanup note:', e);
      }
    }
    setProfile(null);
    setActiveQuery(null);
    setActiveTab('chat');
  };

  return (
    <div className="h-screen w-full flex flex-col bg-slate-50 text-slate-800 overflow-hidden">
      {/* Top Navigation */}
      <Navbar
        profile={profile}
        llmConfigured={llmConfigured}
        onReset={handleResetSession}
        onOpenPreview={() => setIsPreviewModalOpen(true)}
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Main Content Area */}
      <main className="flex-1 w-full p-3 sm:p-5 lg:p-6 overflow-hidden flex flex-col min-h-0">
        {!profile ? (
          <div className="flex-1 flex items-center justify-center overflow-y-auto py-8">
            <FileUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        ) : (
          <div className="flex-1 w-full h-full flex flex-row gap-5 overflow-hidden min-h-0">
            {/* Left Sidebar (Visible on desktop if open, or on mobile when activeTab is dataset) */}
            <div
              className={`h-full flex-shrink-0 ${
                isSidebarOpen ? 'lg:flex' : 'lg:hidden'
              } ${activeTab === 'dataset' ? 'flex w-full' : 'hidden'}`}
            >
              <DatasetSidebar
                profile={profile}
                onSelectQuery={(q) => {
                  setActiveQuery(q);
                  setActiveTab('chat');
                }}
                onOpenMappingsModal={() => setIsMappingsModalOpen(true)}
                onOpenPreview={() => setIsPreviewModalOpen(true)}
              />
            </div>

            {/* Main Chatbot Workspace (Always visible on desktop, or on mobile when activeTab is chat) */}
            <div
              className={`flex-1 h-full min-w-0 ${
                activeTab === 'chat' ? 'flex' : 'hidden lg:flex'
              } flex-col`}
            >
              <ChatInterface
                profile={profile}
                initialQuery={activeQuery}
                onClearInitialQuery={() => setActiveQuery(null)}
                isSidebarOpen={isSidebarOpen}
                onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
              />
            </div>
          </div>
        )}
      </main>

      {/* Modals */}
      {profile && (
        <>
          <SchemaMappingModal
            profile={profile}
            isOpen={isMappingsModalOpen}
            onClose={() => setIsMappingsModalOpen(false)}
            onMappingsUpdated={(updated) => setProfile(updated)}
          />

          <DataPreviewModal
            datasetId={profile.dataset_id}
            isOpen={isPreviewModalOpen}
            onClose={() => setIsPreviewModalOpen(false)}
          />
        </>
      )}
    </div>
  );
};

export default App;
