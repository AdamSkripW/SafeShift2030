import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: 'start',
    loadComponent: () => import('./components/start-page/start-page.component').then(m => m.StartPageComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./components/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'shift/new',
    loadComponent: () => import('./components/new-shift/new-shift.component').then(m => m.NewShiftComponent)
  },
  {
    path: 'shifts',
    loadComponent: () => import('./components/shifts-dashboard/shifts-dashboard.component').then(m => m.ShiftsDashboardComponent)
  },
  {
    path: 'employees',
    loadComponent: () => import('./components/employees/employees.component').then(m => m.EmployeesComponent)
  },
  {
    path: '',
    redirectTo: '/start',
    pathMatch: 'full'
  }
];
