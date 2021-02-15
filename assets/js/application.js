const images = require.context('../images', true)
const imagePath = (name) => images(name, true)

require.context('govuk-frontend/govuk/assets');
import { initAll } from 'govuk-frontend';
initAll();
