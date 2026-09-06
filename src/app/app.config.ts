import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { authInterceptor } from './core/auth/auth.interceptor';
import { routes } from './app.routes';
import { environment } from '../environments/environment';

// Provider interfaces
import { FloodDataProvider } from './core/providers/interfaces/flood-data.provider';
import { AlertDataProvider } from './core/providers/interfaces/alert-data.provider';
import { RoutingDataProvider } from './core/providers/interfaces/routing-data.provider';
import { AnalyticsDataProvider } from './core/providers/interfaces/analytics-data.provider';
import { SystemStatusDataProvider } from './core/providers/interfaces/system-status-data.provider';

// Mock implementations (Phase 1)
import { MockFloodDataProvider } from './core/providers/mock/mock-flood-data.provider';
import { MockAlertDataProvider } from './core/providers/mock/mock-alert.provider';
import { MockRoutingDataProvider } from './core/providers/mock/mock-routing.provider';
import { MockAnalyticsDataProvider } from './core/providers/mock/mock-analytics.provider';
import { MockSystemStatusDataProvider } from './core/providers/mock/mock-system-status.provider';

// FastAPI implementations (Phase 2 ready)
import { FastApiFloodDataProvider } from './core/providers/fastapi/fastapi-flood-data.provider';
import { FastApiAlertDataProvider } from './core/providers/fastapi/fastapi-alert-data.provider';
import { FastApiRoutingDataProvider } from './core/providers/fastapi/fastapi-routing-data.provider';
import { FastApiAnalyticsDataProvider } from './core/providers/fastapi/fastapi-analytics-data.provider';
import { FastApiSystemStatusDataProvider } from './core/providers/fastapi/fastapi-system-status.provider';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor])),

    // Adapter Layer Dependency Injection
    {
      provide: FloodDataProvider,
      useClass: environment.useMockData ? MockFloodDataProvider : FastApiFloodDataProvider
    },
    {
      provide: AlertDataProvider,
      useClass: environment.useMockData ? MockAlertDataProvider : FastApiAlertDataProvider
    },
    {
      provide: RoutingDataProvider,
      useClass: environment.useMockData ? MockRoutingDataProvider : FastApiRoutingDataProvider
    },
    {
      provide: AnalyticsDataProvider,
      useClass: environment.useMockData ? MockAnalyticsDataProvider : FastApiAnalyticsDataProvider
    },
    {
      provide: SystemStatusDataProvider,
      useClass: environment.useMockData ? MockSystemStatusDataProvider : FastApiSystemStatusDataProvider
    }
  ]
};
