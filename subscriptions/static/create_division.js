const category_element = document.getElementById('id_category');

let win;

if (category_element) {
    // add a create button after the category input field
    const add_category_button = document.createElement("button");
    add_category_button.setAttribute("type", "button");
    add_category_button.setAttribute("onclick", "win = window.open('/subs/createCategory', 'newwindow', 'width=1000,height=480'); return false;");
    add_category_button.setAttribute("id", "create_category");
    add_category_button.innerHTML = "+";
    category_element.parentNode.insertBefore(add_category_button, category_element.nextSibling);
}

function checkClosedStatus() {
    if (win && win.closed) {
        location.reload();
    } else {
        requestAnimationFrame(checkClosedStatus);
    }
}

checkClosedStatus();
