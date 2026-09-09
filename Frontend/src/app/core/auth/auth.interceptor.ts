import { HttpInterceptorFn, HttpErrorResponse, HttpRequest, HttpHandlerFn, HttpEvent } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from './auth.service';
import { catchError, switchMap, throwError, Observable } from 'rxjs';

const SKIP_AUTH_URLS = ['/auth/login', '/auth/register', '/auth/refresh', '/otp/'];

function shouldSkip(url: string): boolean {
  return SKIP_AUTH_URLS.some((part) => url.includes(part));
}

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.token();

  let authReq = req;
  if (token && !shouldSkip(req.url)) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401 || shouldSkip(req.url)) {
        return throwError(() => error);
      }
      // Access token expired/invalid: try one silent refresh, then retry.
      return tryRefreshAndRetry(authService, req, next);
    })
  );
};

function tryRefreshAndRetry(
  authService: AuthService,
  req: HttpRequest<unknown>,
  next: HttpHandlerFn
): Observable<HttpEvent<unknown>> {
  return authService.refreshAccessToken().pipe(
    switchMap((newToken) => {
      const retried = req.clone({
        setHeaders: { Authorization: `Bearer ${newToken}` }
      });
      return next(retried);
    }),
    catchError((refreshError) => {
      // Refresh failed (expired/revoked): force re-login.
      authService.logout();
      return throwError(() => refreshError);
    })
  );
}
