import { provideHttpClient } from "@angular/common/http";
import {
  ApplicationConfig,
  provideAppInitializer,
  inject,
} from "@angular/core";
import { provideRouter } from "@angular/router";
import { AppConfigService } from "./core/api/app-config.service";
import { routes } from "./app.routes";

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(),
    provideRouter(routes),
    provideAppInitializer(() => inject(AppConfigService).load()),
  ],
};
