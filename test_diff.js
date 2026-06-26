const Diff = require('diff');
const { Diff2Html } = require('diff2html');

function testDiff(original, modified) {
    console.log("Original:", original);
    console.log("Modified:", modified);
    const patch = Diff.createTwoFilesPatch("Source A", "Source B", original, modified);
    console.log("Patch:", patch);
    const diffHtml = Diff2Html.html(patch, { 
        drawFileList: false, 
        matching: 'lines', 
        outputFormat: 'side-by-side',
        renderNothingWhenEmpty: false
    });
    console.log("HTML length:", diffHtml.length);
    console.log("HTML:", diffHtml);
}

// Case 1: Identical files
testDiff("Hello", "Hello");

// Case 2: Different files
testDiff("Hello", "Hello World");
