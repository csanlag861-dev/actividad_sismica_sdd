import { Component, OnInit, signal } from "@angular/core";
import { RouterLink, RouterLinkActive, RouterOutlet } from "@angular/router";
import { SeismicTheme } from "./core/models/ui-state.models";
import { QueryStateService } from "./core/state/query-state.service";

@Component({
  selector: "app-root",
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: "./app.component.html",
  styleUrl: "./app.component.css",
})
export class AppComponent implements OnInit {
  readonly theme = signal<SeismicTheme>("dark");

  constructor(readonly queries: QueryStateService) {}

  ngOnInit(): void {
    document.documentElement.dataset["theme"] = this.theme();
    void this.queries.refresh();
  }

  toggleTheme(): void {
    const nextTheme = this.theme() === "dark" ? "light" : "dark";
    this.theme.set(nextTheme);
    document.documentElement.dataset["theme"] = nextTheme;
  }
}
