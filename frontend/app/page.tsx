'use client';

import { useState } from 'react';
import { 
  Sparkles, 
  FileText, 
  Briefcase, 
  ArrowRight, 
  Copy, 
  CheckCircle2, 
  Zap 
} from 'lucide-react';

export default function Home() {
  const [cvText, setCvText] = useState('');
  const [jobDesc, setJobDesc] = useState('');
  const [optimizedCv, setOptimizedCv] = useState('');
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleOptimize = async () => {
    if (!cvText) return;
    setLoading(true);
    setOptimizedCv('');
    
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cv_text: cvText, job_description: jobDesc }),
      });
      const data = await res.json();
      if (data.optimized_text) setOptimizedCv(data.optimized_text);
    } catch (e) {
      alert("Erreur de connexion au cerveau de l'IA.");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(optimizedCv);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-blue-50 text-slate-800 font-sans selection:bg-indigo-100">
      
      {/* Navbar Minimaliste */}
      <nav className="border-b border-indigo-100 bg-white/50 backdrop-blur-md sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-indigo-600 p-1.5 rounded-lg">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl tracking-tight text-indigo-950">Aria<span className="text-indigo-600">CV</span></span>
          </div>
          <div className="text-xs font-medium text-indigo-400 bg-indigo-50 px-3 py-1 rounded-full border border-indigo-100">
            Powered by Mistral AI
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-2 gap-10">
        
        {/* COLONNE GAUCHE : INPUTS */}
        <div className="flex flex-col gap-6 animate-in slide-in-from-left duration-700">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 mb-2">Optimisez votre impact.</h1>
            <p className="text-slate-500">L'IA analyse et reformule votre CV pour correspondre parfaitement aux attentes des recruteurs.</p>
          </div>

          {/* Card CV */}
          <div className="bg-white p-1 rounded-2xl shadow-sm border border-slate-200 focus-within:ring-2 focus-within:ring-indigo-500 transition-all">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100">
              <FileText className="w-4 h-4 text-indigo-500" />
              <span className="text-sm font-semibold text-slate-700">Votre CV actuel</span>
            </div>
            <textarea 
              value={cvText}
              onChange={(e) => setCvText(e.target.value)}
              placeholder="Collez le contenu texte de votre CV ici..."
              className="w-full h-48 p-4 bg-transparent border-none outline-none resize-none text-sm text-slate-600 placeholder:text-slate-300"
            />
          </div>

          {/* Card Job Desc */}
          <div className="bg-white p-1 rounded-2xl shadow-sm border border-slate-200 focus-within:ring-2 focus-within:ring-indigo-500 transition-all">
            <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-100">
              <Briefcase className="w-4 h-4 text-indigo-500" />
              <span className="text-sm font-semibold text-slate-700">Offre d'emploi (Optionnel)</span>
            </div>
            <textarea 
              value={jobDesc}
              onChange={(e) => setJobDesc(e.target.value)}
              placeholder="Collez la description du poste pour une adaptation contextuelle..."
              className="w-full h-32 p-4 bg-transparent border-none outline-none resize-none text-sm text-slate-600 placeholder:text-slate-300"
            />
          </div>

          <button
            onClick={handleOptimize}
            disabled={!cvText || loading}
            className={`
              group relative overflow-hidden rounded-xl py-4 font-semibold text-white shadow-lg transition-all
              ${!cvText || loading ? 'bg-slate-300 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700 hover:shadow-indigo-200 hover:-translate-y-0.5'}
            `}
          >
            <div className="relative z-10 flex items-center justify-center gap-2">
              {loading ? (
                <>
                  <Zap className="w-5 h-5 animate-pulse" />
                  <span>Analyse en cours...</span>
                </>
              ) : (
                <>
                  <span>Générer la version optimisée</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </div>
          </button>
        </div>

        {/* COLONNE DROITE : RESULTAT */}
        <div className={`relative flex flex-col h-full min-h-[500px] animate-in slide-in-from-right duration-700 delay-100`}>
          
          <div className="absolute inset-0 bg-white rounded-2xl shadow-xl border border-slate-200/60 overflow-hidden flex flex-col">
            
            {/* Header Résultat */}
            <div className="bg-slate-50/80 backdrop-blur border-b border-slate-100 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${optimizedCv ? 'bg-green-500' : 'bg-slate-300'}`} />
                <span className="font-semibold text-slate-700">Résultat IA</span>
              </div>
              
              {optimizedCv && (
                <button 
                  onClick={copyToClipboard}
                  className="flex items-center gap-1.5 text-xs font-medium text-indigo-600 hover:bg-indigo-50 px-3 py-1.5 rounded-lg transition-colors"
                >
                  {copied ? <CheckCircle2 className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copié !' : 'Copier'}
                </button>
              )}
            </div>

            {/* Contenu */}
            <div className="flex-1 overflow-y-auto p-8 bg-white relative">
              {optimizedCv ? (
                <div className="prose prose-sm max-w-none text-slate-700 leading-relaxed whitespace-pre-wrap">
                  {optimizedCv}
                </div>
              ) : (
                <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-300 gap-4">
                  <div className="w-16 h-16 rounded-full bg-slate-50 border border-slate-100 flex items-center justify-center">
                    <Sparkles className="w-8 h-8 opacity-20" />
                  </div>
                  <p className="text-sm font-medium">Le résultat apparaîtra ici</p>
                </div>
              )}
            </div>
          </div>
          
          {/* Décoration d'arrière plan (bruit de fond) */}
          <div className="absolute -z-10 top-10 -right-10 w-64 h-64 bg-indigo-500/10 rounded-full blur-3xl" />
          <div className="absolute -z-10 bottom-10 -left-10 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl" />
        </div>

      </main>
    </div>
  );
}