import { Observable } from 'rxjs';
import { AdminSystemOverview } from '../../models/system-status.model';

export abstract class SystemStatusDataProvider {
  abstract getSystemOverview(): Observable<AdminSystemOverview>;
}
