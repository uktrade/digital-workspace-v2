import './components/accordion';
import './components/copy_text';
import './components/cta_button';
import './components/menu_vertical';
import './components/modal';
import './components/page_react_button';
import './components/toggle_visibility_button';
import { DWDSLinks } from './components/links';
import './elements/ribbon';

export class DigitalWorkspaceDesignSystem {
    constructor() { }

    initAll() {
        new DWDSLinks().initAll();
    }
}
