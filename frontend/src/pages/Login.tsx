import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      // OAuth2PasswordRequestForm expects x-www-form-urlencoded
      const form = new URLSearchParams();
      form.append('username', username);
      form.append('password', password);
      const res = await fetch('/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: form.toString(),
      });
      if (!res.ok) throw new Error('Invalid credentials');
      const data = await res.json();
      localStorage.setItem('auth_token', data.access_token);
      toast.success('Logged in');
      navigate('/');
    } catch (err: any) {
      toast.error(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
      <div className="bg-white shadow rounded-lg p-6 w-full max-w-sm">
        <h1 className="text-xl font-semibold mb-4">Sign in</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email or Username</label>
            <input value={username} onChange={(e) => setUsername(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <button type="submit" disabled={loading} className={`w-full px-4 py-2 text-sm font-medium text-white rounded-md ${loading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}>{loading ? 'Signing in...' : 'Sign in'}</button>
        </form>
      </div>
    </div>
  );
};

export default Login;


