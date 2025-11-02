import React, { useState } from 'react';
import { VoiceInput } from './VoiceInput';
import { notificationService } from '../services/notificationService';

export const VoiceInputTest: React.FC = () => {
  const [transcript, setTranscript] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('en-US');

  const handleTranscript = (text: string) => {
    setTranscript(prev => prev + ' ' + text);
    console.log('Transcript received:', text);
  };

  const handleError = (error: string) => {
    console.error('Voice input error:', error);
    notificationService.error(error);
  };

  const handleLanguageChange = (language: string) => {
    setSelectedLanguage(language);
    console.log('Language changed to:', language);
  };

  const clearTranscript = () => {
    setTranscript('');
  };

  return (
    <div className="max-w-2xl mx-auto p-6 bg-slate-900 rounded-lg">
      <h2 className="text-2xl font-bold text-white mb-6">Voice Input Test</h2>
      
      <div className="space-y-6">
        {/* Current Language Display */}
        <div className="bg-slate-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-2">Current Settings</h3>
          <p className="text-slate-300">Selected Language: <span className="text-blue-400">{selectedLanguage}</span></p>
        </div>

        {/* Voice Input Component */}
        <div className="bg-slate-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-4">Voice Input</h3>
          <VoiceInput
            onTranscript={handleTranscript}
            onError={handleError}
            language={selectedLanguage}
            showLanguageSelector={true}
            onLanguageChange={handleLanguageChange}
            className="w-full"
          />
        </div>

        {/* Transcript Display */}
        <div className="bg-slate-800 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Transcript</h3>
            <button
              onClick={clearTranscript}
              className="px-3 py-1 bg-red-500 hover:bg-red-600 text-white rounded text-sm transition-colors"
            >
              Clear
            </button>
          </div>
          <div className="min-h-[100px] p-3 bg-slate-700 rounded border border-slate-600">
            {transcript ? (
              <p className="text-slate-200 whitespace-pre-wrap">{transcript}</p>
            ) : (
              <p className="text-slate-400 italic">No transcript yet. Try speaking into the microphone.</p>
            )}
          </div>
        </div>

        {/* Instructions */}
        <div className="bg-blue-500/10 border border-blue-500/30 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-400 mb-2">Instructions</h3>
          <ul className="text-slate-300 space-y-1 text-sm">
            <li>1. Select your preferred language from the dropdown</li>
            <li>2. Click the microphone button to start recording</li>
            <li>3. Speak clearly into your microphone</li>
            <li>4. Click the stop button or wait for automatic stop</li>
            <li>5. The transcript will appear below</li>
          </ul>
        </div>

        {/* Debug Info */}
        <div className="bg-slate-800 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-white mb-2">Debug Info</h3>
          <div className="text-sm text-slate-400 space-y-1">
            <p>Default Language: en-US (English US)</p>
            <p>Language Selector: Enabled</p>
            <p>Transcript Length: {transcript.length} characters</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VoiceInputTest;