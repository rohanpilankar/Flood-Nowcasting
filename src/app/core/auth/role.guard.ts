import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService, UserRole } from './auth.service';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url }
    });
  }

  const expectedRoles = (route.data?.['roles'] || []) as UserRole[];
  const userRole = authService.userRole();

  if (!expectedRoles.length || (userRole && expectedRoles.includes(userRole))) {
    return true;
  }

  // Not authorized for this role, redirect to appropriate home
  if (userRole === 'CITIZEN') {
    return router.createUrlTree(['/citizen/dashboard']);
  } else if (userRole?.startsWith('GOVERNMENT_')) {
    return router.createUrlTree(['/government/dashboard']);
  } else if (userRole === 'ADMIN') {
    return router.createUrlTree(['/admin']);
  }

  return router.createUrlTree(['/dashboard']);
};
