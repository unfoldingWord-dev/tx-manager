var markdownlint = require("markdownlint");

exports.handle = function(e, ctx, cb) {
    var result = markdownlint.sync(e.options);
    cb(null, result);
};
