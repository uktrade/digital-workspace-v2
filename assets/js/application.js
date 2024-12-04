import "htmx.org/dist/htmx.js";

const images = require.context("../images", true);
const imagePath = (name) => images(name, true);

require.context("govuk-frontend/govuk/assets");
require.context(
    "@ministryofjustice/frontend/moj/assets"
);
import { initAll } from "govuk-frontend";
import mojFrontend from "@ministryofjustice/frontend";

initAll();
mojFrontend.initAll();

if (typeof window.djdt !== "undefined" && typeof window.htmx !== "undefined") {
    htmx.on("htmx:afterSettle", function (detail) {
        if (detail.target instanceof HTMLBodyElement) {
            djdt.show_toolbar();
        }
    });
}