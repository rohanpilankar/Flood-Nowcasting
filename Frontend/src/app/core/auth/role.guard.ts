import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService, UserRole } from './auth.service';
import { of, map, catchError, Observable } from 'rxjs';

function roleRedirect(router: Router, userRole: UserRole | null): UrlTree {
  // Not authorized for this role, redirect to appropriate home
  if (userRole === 'CITIZEN') {
    return router.createUrlTree(['/citizen/dashboard']);
  } else if (userRole?.startsWith('GOVERNMENT_')) {
    return router.createUrlTree(['/government/dashboard']);
  } else if (userRole === 'ADMIN') {
    return router.createUrlTree(['/admin']);
  }
  return router.createUrlTree(['/dashboard']);
}

function checkRole(
  authService: AuthService,
  router: Router,
  route: Parameters<CanActivateFn>[0]
): boolean | UrlTree {
  const expectedRoles = (route.data?.['roles'] || []) as UserRole[];
  const userRole = authService.userRole();

  if (!expectedRoles.length || (userRole && expectedRoles.includes(userRole))) {
    return true;
  }
  return roleRedirect(router, userRole);
}

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const loginTree = router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url }
  });

  if (authService.hasValidToken() && authService.currentUser()) {
    return checkRole(authService, router, route);
  }

  // Try silent refresh before redirecting to login.
  if (authService.getRefreshToken()) {
    const result: Observable<boolean | UrlTree> = authService.refreshAccessToken().pipe(
      map(() => checkRole(authService, router, route)),
      catchError(() => of(loginTree))
    );
    return result;
  }

  return loginTree;
};
