const fs = require('fs');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;
const Diff = require('diff');
const { Diff2Html } = require('diff2html');

const html = fs.readFileSync('docfinder_frontend/results.html', 'utf-8');

const html = fs.readFileSync('docfinder_frontend/results.html', 'utf-8');

const { window } = new JSDOM('', { url: "http://localhost/" });

window.localStorage.setItem('token', 'test');
window.localStorage.setItem('user', 'test');
window.localStorage.setItem('lastResult', JSON.stringify({
    fileType: 'text',
    mode: 'normal',
    results: {
        similarity_score: 0.67,
        total_additions: 20,
        total_deletions: 3,
        total_modifications: 0,
        full_text1: "A",
        full_text2: "B"
    }
}));
window.localStorage.setItem('lastTexts', JSON.stringify({
    text1: "A",
    text2: "B"
}));

window.Diff = Diff;
window.Diff2Html = {
    html: (patch, options) => {
        try {
            return Diff2Html.html(patch, options);
        } catch (e) {
            console.error(e);
            return "ERROR";
        }
    }
};

const dom = new JSDOM(html, { runScripts: "dangerously", url: "http://localhost/", beforeParse(window) {
    Object.assign(window.localStorage, window.localStorage); // copy over
    // Better way: just use virtual console
} });
// Just inject into the real dom
dom.window.localStorage.setItem('token', 'test');
dom.window.localStorage.setItem('user', 'test');
dom.window.localStorage.setItem('lastResult', JSON.stringify({
    fileType: 'text',
    mode: 'normal',
    results: {
        similarity_score: 0.67,
        total_additions: 20,
        total_deletions: 3,
        total_modifications: 0,
        full_text1: "A",
        full_text2: "B"
    }
}));
dom.window.localStorage.setItem('lastTexts', JSON.stringify({
    text1: "A",
    text2: "B"
}));
dom.window.Diff = Diff;
dom.window.Diff2Html = { html: (patch, options) => Diff2Html.html(patch, options) };
// Re-evaluate script
const script = dom.window.document.querySelector('script:last-of-type').textContent;
dom.window.eval(script);

setTimeout(() => {
    console.log("Diff Body HTML:", dom.window.document.getElementById('diffBody').innerHTML);
    console.log("AI Analysis:", dom.window.document.getElementById('aiAnalysis').innerHTML);
}, 1000);
