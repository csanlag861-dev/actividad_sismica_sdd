import { Injectable } from "@angular/core";
import type { Viewer } from "cesium";

declare global {
  interface Window {
    CESIUM_BASE_URL?: string;
  }
}

@Injectable({ providedIn: "root" })
export class Globe3DViewerService {
  private cesium: typeof import("cesium") | null = null;
  private widgetStyles: HTMLLinkElement | null = null;

  get library(): typeof import("cesium") {
    if (!this.cesium) throw new Error("CesiumJS no está inicializado.");
    return this.cesium;
  }

  async createViewer(container: HTMLElement): Promise<Viewer> {
    window.CESIUM_BASE_URL = "/assets/cesium/";
    let viewer: Viewer | null = null;
    try {
      const Cesium = await import("cesium");
      this.cesium = Cesium;
      this.widgetStyles = document.createElement("link");
      this.widgetStyles.rel = "stylesheet";
      this.widgetStyles.href = "/assets/cesium/Widgets/widgets.css";
      this.widgetStyles.dataset["cesiumWidgetStyles"] = "true";
      document.head.append(this.widgetStyles);

      const baseLayer = new Cesium.ImageryLayer(new Cesium.OpenStreetMapImageryProvider({
        url: "https://tile.openstreetmap.org/",
      }));
      viewer = new Cesium.Viewer(container, {
        baseLayer,
        baseLayerPicker: false,
        animation: false,
        fullscreenButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        navigationHelpButton: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
      });
      viewer.camera.setView({
        destination: Cesium.Cartesian3.fromDegrees(0, 15, 20_000_000),
      });
      return viewer;
    } catch (error) {
      this.destroy(viewer);
      throw error;
    }
  }

  destroy(viewer: Viewer | null): void {
    if (viewer && !viewer.isDestroyed()) viewer.destroy();
    this.widgetStyles?.remove();
    this.widgetStyles = null;
    this.cesium = null;
  }
}
