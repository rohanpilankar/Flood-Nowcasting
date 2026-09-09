import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from './auth.service';
import { of, map, catchError } from 'rxjs';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);
  const loginTree = router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url }
  });

  // Valid access token: allow immediately.
  if (authService.hasValidToken() && authService.currentUser()) {
    return true;
  }

  // Expired/missing access token but a refresh token exists:
  // attempt one silent refresh before bouncing to /login.
  if (authService.getRefreshToken()) {
    return authService.refreshAccessToken().pipe(
      map(() => true),
      catchError(() => of(loginTree))
    );
  }

  // Redirect to login page with return url
  return loginTree;
};
