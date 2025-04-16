document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.dwds-menu-vertical').forEach(function (element) {
        const table_of_contents = element.getElementsByClassName('page-toc')[0];

        if (!table_of_contents) {
            return;
        }

        const headings_selector = 'h2, h3, h4';
        const main_page_content = document.querySelector('main .primary-content');
        const headings_elements = main_page_content.querySelectorAll(headings_selector);
        headings_elements.forEach(function (heading_element) {
            const heading_text = heading_element.textContent;
            const heading_id = heading_element.id;

            if (!heading_id) {
                return;
            }

            const heading_link = document.createElement('a');
            heading_link.href = '#' + heading_id;
            heading_link.textContent = heading_text;

            const heading_item = document.createElement("li");
            heading_item.appendChild(heading_link);
            table_of_contents.appendChild(heading_item);
        });
    });
});