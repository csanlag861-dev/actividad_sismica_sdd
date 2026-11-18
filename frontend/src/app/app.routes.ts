import { Routes } from "@angular/router";
import { DashboardPageComponent } from "./features/dashboard/dashboard-page.component";
import { EventsPageComponent } from "./features/events/events-page.component";
import { AnalyticsPageComponent } from "./features/analytics/analytics-page.component";

export const routes: Routes = [
  { path: "", component: DashboardPageComponent, title: "Resumen | Observatorio sísmico" },
  { path: "eventos", component: EventsPageComponent, title: "Exploración | Observatorio sísmico" },
  { path: "analisis", component: AnalyticsPageComponent, title: "Análisis | Observatorio sísmico" },
  { path: "**", redirectTo: "" },
];
