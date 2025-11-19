export interface User {
  id: string;
  username: string;
  name: string;
  role: 'admin' | 'driver' | 'manager' | 'customer';
}

export interface LoginState {
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
  user: User | null;
}

export interface SystemStatus {
  isOnline: boolean;
  version: string;
}
