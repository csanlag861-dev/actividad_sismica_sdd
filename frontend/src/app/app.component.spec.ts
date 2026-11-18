import { TestBed } from "@angular/core/testing";
import { provideRouter } from "@angular/router";
import { AppComponent } from "./app.component";
import { routes } from "./app.routes";
import { QueryStateService } from "./core/state/query-state.service";

describe("AppComponent", () => {
  let refresh: jasmine.Spy;

  beforeEach(async () => {
    refresh = jasmine.createSpy("refresh").and.resolveTo(undefined);
    await TestBed.configureTestingModule({
      imports: [AppComponent],
      providers: [
        provideRouter(routes),
        { provide: QueryStateService, useValue: { refresh } },
      ],
    }).compileComponents();
  });

  afterEach(() => {
    delete document.documentElement.dataset["theme"];
  });

  it("starts on the dashboard and requests the initial resources", () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('a[href="/"]')).toBeTruthy();
    const logo = fixture.nativeElement.querySelector(".brand-logo") as HTMLImageElement;
    expect(logo.src).toContain("/icon.png");
    expect(logo.alt).toBe("Logo del Observatorio de actividad sísmica");
    expect(fixture.nativeElement.querySelector('a[href="/eventos"]')).toBeTruthy();
    expect(fixture.nativeElement.querySelector('a[href="/analisis"]')).toBeTruthy();
    expect(refresh).toHaveBeenCalledTimes(1);
  });

  it("toggles the theme in memory without persisting user preferences", () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;
    const storedItemsBefore = localStorage.length;

    expect(document.documentElement.dataset["theme"]).toBe("dark");
    component.toggleTheme();
    expect(component.theme()).toBe("light");
    expect(document.documentElement.dataset["theme"]).toBe("light");
    expect(localStorage.length).toBe(storedItemsBefore);
  });

  it("keeps the logo proportionate and accessible in both themes", () => {
    const fixture = TestBed.createComponent(AppComponent);
    fixture.detectChanges();
    const logo = fixture.nativeElement.querySelector(".brand-logo") as HTMLImageElement;
    const component = fixture.componentInstance;

    expect(logo.alt).toBeTruthy();
    expect(getComputedStyle(logo).objectFit).toBe("contain");
    expect(getComputedStyle(logo).width).toBe("40px");
    component.toggleTheme();
    fixture.detectChanges();
    expect(component.theme()).toBe("light");
    expect(getComputedStyle(logo).objectFit).toBe("contain");
    expect(getComputedStyle(logo).width).toBe("40px");
  });
});
