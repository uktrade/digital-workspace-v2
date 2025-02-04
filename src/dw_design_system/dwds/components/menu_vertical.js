document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-menu-vertical').forEach(function (element) {
        let table_of_contents = element.getElementsByClassName('.page-toc')[0];

        if (!table_of_contents) {
            return;
        }

        let headings_selector = 'h2, h3, h4';
        let main_page_content = document.querySelector('main .primary-content');
        let headings_elements = main_page_content.querySelectorAll(headings_selector);
        headings_elements.forEach(function (heading_element) {
            let heading_text = heading_element.textContent;
            let heading_id = heading_element.id;

            if (!heading_id) {
                return;
            }

            let heading_link = document.createElement('a');
            heading_link.href = '#' + heading_id;
            heading_link.textContent = heading_text;

            let heading_item = document.createElement("li");
            heading_item.appendChild(heading_link);
            table_of_contents.appendChild(heading_item);
        });
    });
});