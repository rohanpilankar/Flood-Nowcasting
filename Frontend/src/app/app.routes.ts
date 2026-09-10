import { Routes } from '@angular/router';
import { authGuard } from './core/auth/auth.guard';
import { roleGuard } from './core/auth/role.guard';

export const routes: Routes = [
  // Landing / Hero Page (Root)
  {
    path: '',
    loadComponent: () => import('./features/landing/landing.component').then(m => m.LandingComponent),
    title: 'FloodWatch AI — AI-Powered Urban Flood Nowcasting & Safe Mobility'
  },
  {
    path: 'home',
    redirectTo: '',
    pathMatch: 'full'
  },
  // Auth Routes
  {
    path: 'login',
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent),
    title: 'FloodWatch AI — Unified Portal Login'
  },
  {
    path: 'register',
    loadComponent: () => import('./features/auth/register/register.component').then(m => m.RegisterComponent),
    title: 'FloodWatch AI — Citizen Safety Registration'
  },

  // Citizen Protected Routes
  {
    path: 'citizen/dashboard',
    loadComponent: () => import('./features/citizen/citizen-dashboard/citizen-dashboard.component').then(m => m.CitizenDashboardComponent),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['CITIZEN', 'ADMIN'] },
    title: 'FloodWatch AI — Citizen Safety Portal'
  },
  {
    path: 'citizen/my-alerts',
    loadComponent: () => import('./features/citizen/my-alerts/my-alerts.component').then(m => m.MyAlertsComponent),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['CITIZEN', 'ADMIN'] },
    title: 'FloodWatch AI — My Targeted Warnings'
  },
  {
    path: 'citizen/privacy',
    loadComponent: () => import('./features/citizen/privacy-settings/privacy-settings.component').then(m => m.PrivacySettingsComponent),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['CITIZEN', 'ADMIN'] },
    title: 'FloodWatch AI — Privacy & Monitored Places'
  },

  // Government Authority Protected Routes
  {
    path: 'government/dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['GOVERNMENT_VIEWER', 'GOVERNMENT_OPERATOR', 'GOVERNMENT_SUPERVISOR', 'ADMIN'] },
    title: 'FloodWatch AI — GCC Operational Flood Dashboard'
  },

  // Public / Monitored Operations
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
    title: 'FloodWatch AI — GCC Operational Flood Dashboard & Prediction Console'
  },
  {
    path: 'drainage',
    loadComponent: () => import('./features/drainage/drainage.component').then(m => m.DrainageComponent),
    title: 'FloodWatch AI — 3D Drainage Network & Manning Hydraulics'
  },
  {
    path: 'simulation',
    loadComponent: () => import('./features/simulation/simulation.component').then(m => m.SimulationComponent),
    title: 'FloodWatch AI — Model Simulation & Storm Scenario Studio'
  },
  {
    path: 'flood-map',
    loadComponent: () => import('./features/flood-map/flood-map.component').then(m => m.FloodMapComponent),
    title: 'FloodWatch AI — Greater Chennai GIS Flood Risk Map'
  },
  {
    path: 'location-risk',
    loadComponent: () => import('./features/location-risk/location-risk.component').then(m => m.LocationRiskComponent),
    title: 'FloodWatch AI — Location Risk Analysis'
  },
  {
    path: 'safe-route',
    loadComponent: () => import('./features/safe-route/safe-route.component').then(m => m.SafeRouteComponent),
    title: 'FloodWatch AI — Safe Mobility & Route Planner'
  },
  {
    path: 'alerts',
    loadComponent: () => import('./features/alerts/alerts.component').then(m => m.AlertsComponent),
    title: 'FloodWatch AI — Emergency Alert Operations'
  },
  {
    path: 'analytics',
    loadComponent: () => import('./features/analytics/analytics.component').then(m => m.AnalyticsComponent),
    title: 'FloodWatch AI — AI Inundation Analytics'
  },

  // Admin Command Center (Protected)
  {
    path: 'admin',
    loadComponent: () => import('./features/admin/admin.component').then(m => m.AdminComponent),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['ADMIN'] },
    title: 'FloodWatch AI — Admin & System Operations'
  },
  {
    path: 'settings',
    loadComponent: () => import('./features/settings/settings.component').then(m => m.SettingsComponent),
    title: 'FloodWatch AI — System Settings'
  },
  {
    path: '**',
    redirectTo: 'home'
  }
];
