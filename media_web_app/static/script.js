///////// Elements Constants Variables /////////

// Elelements
const rootElement = document.documentElement;
const browser = document.getElementById("browser");
const searchFormSimple = document.getElementById("search-form-simple");
const searchFormAdvanced = document.getElementById("search-form-advanced");
const searchModeBtn = document.getElementById("search-mode-button");
const newEntryView = document.getElementById("new-entry-page-container");
const newEntryViewBtn = document.getElementById("new-entry-view-button");
const newEntryExitBtn = document.getElementById("new-entry-exit-button");
const newEntryForm = document.querySelector("#new-entry-form");                 // use `querySelector` instead of `getElementById` to access the `HTMLFormElement` methods

// ---
const backendURL = window.location.origin;                                      // gets the url origin (protocol, hostname, and port) of the URL (to be used to make further requests)
const fileTypeThumbnailMap = {
    movie: "./static/resources/file_icon_500_500.svg",
    show: "./static/resources/file_icon_500_500.svg",
    music: "./static/resources/file_icon_500_500.svg",
    book: "./static/resources/file_icon_500_500.svg"
};


///////// Functions /////////

async function getRecentMediaEntries() {
    const response = await fetch(backendURL + "/api/recent", {
        method: "GET",
        mode: "cors",
    });
    const entries = await response.json();
    return entries;
};

function createFileElement(title, type, description, imgSource) {
    // get source for thumbnail
    let thumbnail;
    if (imgSource) {thumbnail = imgSource} else {thumbnail = fileTypeThumbnailMap[type]};
    // create the html
    let fileElementHTML = `
    <img class="file-thumbnail" src="${thumbnail}" alt="file thumbnail image">
    <div class="file-text">
        <span class="file-title">${title}</span>
        <p class="file-description">${description}</p>
    </div>
    <div class="file-controls">
        <button class="file-download" type="button">DOWNLOAD</button>
        <!-- <button class="file-edit" type="button">edit</button> -->
    </div>
    `
    // <div class="file-title-bar">
    //     <img class="file-thumbnail" src="${thumbnail}" alt="file thumbnail image">
    //     <span class="file-title">${title}</span>
    // </div>

    // create all file html elements
    let fileDiv = document.createElement('div')
    fileDiv.classList.add("file", "bordered")
    fileDiv.insertAdjacentHTML('afterbegin', fileElementHTML)
    return fileDiv
};

async function renderMediaEntries(entries) {
    if (entries.length > 0) {                                                   // if entries is not empty:
        browser.innerHTML = "";                                                 // first, clear everything from browser
        for (const entry of entries) {
            // set element content to be data from media entries
            let fileDiv = createFileElement(entry['title'], entry['type'], entry['description'])
            browser.appendChild(fileDiv)
        };
    } else {
        browser.innerHTML = '<span class="message">No results found</span?'     // otherwise if entries is empty, do no results found
    }
};

// Toggle menu display between simple and advanced search mode
function toggleSearchMode(mode) {                                               // `mode` is a string argument. Pass 'simple' for simple, 'advanced' for advanced
    if (mode === "simple") {
        searchModeBtn.innerText = "Advanced Search";
        searchFormSimple.style.display = "flex";
        searchFormAdvanced.style.display = "none";
    } else if (mode === "advanced") {
        searchModeBtn.innerText = "Simple Search";
        searchFormSimple.style.display = "none";
        searchFormAdvanced.style.display = "flex";
    }
};

// Toggle between normal view (of browser and menu) and new entry view
function toggleNewEntryView(entry) {                                            // `entry` is a bool argument. Pass `true` to toggle to new-entry view, and `false` for normal
    if (entry) {
        document.body.style.overflow = 'hidden';                                // disable scrolling of browser elements while viewing new entry box
        newEntryView.style.display = "flex";
    } else {
        document.body.style.overflow = 'auto';
        newEntryView.style.display = "none";
    };
};


///////// Listeners /////////

// renders the media entries into the page when loaded
window.addEventListener("load", async () => {
    const entries = await getRecentMediaEntries();
    await renderMediaEntries(entries);
});

// action for the search mode toggle button
searchModeBtn.addEventListener("click", () => {
    if (searchModeBtn.innerText === "Simple Search") {
        toggleSearchMode("simple");
    } else if (searchModeBtn.innerText === "Advanced Search") {
        toggleSearchMode("advanced");
    };
});

// action for the new entry view button
newEntryViewBtn.addEventListener("click", () => {
    toggleNewEntryView(true);
});

// action for new entry exit button
newEntryExitBtn.addEventListener("click", () => {
    toggleNewEntryView(false);
})

// the function to perform for the search-form submit event - get a list of matching entries and render them as file element in the browser
searchFormSimple.addEventListener("submit", async (e) => {
    e.preventDefault();                                                         // by default, the submit event reloaded the page - this line prevents this 
    const data = new FormData(e.target);
    const dataJSON = JSON.stringify(Object.fromEntries(data.entries()))         // converts FormData into object, and then object into JSON string
    try {
        const response = await fetch(backendURL + "/api/general-search", {
            method: "POST",
            mode: "cors",
            headers: {
                "Content-Type": "application/json"                              // lets server know that this is JSON
            },
            body: dataJSON
        });
        var result = await response.json();
    } catch (error) {
        console.log("Error:", error);
    };
    renderMediaEntries(result);
})

// the function to perform for the new-entry submit event - create a new entry based on the form data
newEntryForm.addEventListener("submit", async (e) => {
    e.preventDefault();                                                         // by default, the submit event reloaded the page - this line prevents this 
    const data = new FormData(e.target);
    newEntryForm.reset();                                                       // resets the form
    const dataJSON = JSON.stringify(Object.fromEntries(data.entries()))         // converts FormData into object, and then object into JSON string
    try {
        const response = await fetch(backendURL + "/api/new", {
            method: "POST",
            mode: "cors",
            headers: {
                "Content-Type": "application/json"                              // lets server know that this is JSON
            },
            body: dataJSON
        });
        var result = await response.json();
    } catch (error) {
        console.log("Error:", error);
    };
    renderMediaEntries(result);
    toggleNewEntryView(false);
})


//////////////////////////////////////
///////// Initial Page Setup /////////

toggleSearchMode("simple");
toggleNewEntryView(false);
