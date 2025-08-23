import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Login from './pages/Login';
import RequireAuth from './components/Auth/RequireAuth';
import Dashboard from './pages/Dashboard/Dashboard';
import Lenders from './pages/Lenders/Lenders';
import ApiConfigs from './pages/ApiConfigs/ApiConfigs';
import ApiTemplates from './pages/ApiTemplates/ApiTemplates';
import GeneratedApis from './pages/GeneratedApis/GeneratedApis';
import ApiTests from './pages/ApiTests/ApiTests';
import Users from './pages/Users/Users';
import LenderDetail from './pages/Lenders/LenderDetail';
import LenderNew from './pages/Lenders/LenderNew';
import LenderConfiguration from './pages/Lenders/LenderConfiguration';
import AnalyticsDashboard from './pages/Analytics/AnalyticsDashboard';
import SampleConfigurations from './pages/Samples/SampleConfigurations';
import ApiConfigDetail from './pages/ApiConfigs/ApiConfigDetail';
import GeneratedApiDetail from './pages/GeneratedApis/GeneratedApiDetail';
import Deployments from './pages/Deployments/Deployments';
import './App.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 10000, // 10 seconds
      cacheTime: 300000, // 5 minutes
      refetchOnMount: true,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <RequireAuth>
                  <Layout>
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/lenders" element={<Lenders />} />
                      <Route path="/lenders/new" element={<LenderNew />} />
                      <Route path="/lenders/:id" element={<LenderDetail />} />
                      <Route path="/lenders/:id/configure" element={<LenderConfiguration />} />
                      <Route path="/analytics" element={<AnalyticsDashboard />} />
                      <Route path="/samples" element={<SampleConfigurations />} />
                      <Route path="/api-configs" element={<ApiConfigs />} />
                      <Route path="/api-configs/:id" element={<ApiConfigDetail />} />
                      <Route path="/api-templates" element={<ApiTemplates />} />
                      <Route path="/generated-apis" element={<GeneratedApis />} />
                      <Route path="/generated-apis/:id" element={<GeneratedApiDetail />} />
                      <Route path="/deployments" element={<Deployments />} />
                      <Route path="/api-tests" element={<ApiTests />} />
                      <Route path="/users" element={<Users />} />
                    </Routes>
                  </Layout>
                </RequireAuth>
              }
            />
          </Routes>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
            }}
          />
        </div>
      </Router>
    </QueryClientProvider>
  );
}

export default App;
