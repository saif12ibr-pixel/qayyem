// Behaviour for templates/_answer_fields.html: show only the ideal-answer
// inputs the chosen source uses, and keep a question's maximum score equal to
// the sum of its parts while it is marked in parts.
(function () {
  document.querySelectorAll('[data-ideal-group]').forEach(function (group) {
    var typed = group.querySelector('[data-ideal-typed]');
    var file = group.querySelector('[data-ideal-file]');
    group.querySelectorAll('input[type="radio"]').forEach(function (radio) {
      radio.addEventListener('change', function () {
        typed.hidden = radio.value === 'file';
        file.hidden = radio.value === 'text';
      });
    });
  });

  document.querySelectorAll('[data-parts]').forEach(function (box) {
    var rows = box.querySelector('[data-part-rows]');
    var template = box.querySelector('[data-part-template]');
    var max = document.getElementById(box.dataset.maxInput);

    function update() {
      var marks = rows.querySelectorAll('.part-marks');
      if (!marks.length) {
        max.readOnly = false;
        return;
      }
      var total = 0;
      marks.forEach(function (input) { total += parseFloat(input.value) || 0; });
      max.readOnly = true;
      max.value = total;
      // Lets anything summing the maximum scores, like the exam total, follow.
      max.dispatchEvent(new Event('input', { bubbles: true }));
    }

    function addRow() {
      rows.appendChild(template.content.cloneNode(true));
      update();
    }

    box.querySelector('[data-add-part]').addEventListener('click', function () {
      // Two parts at once: a single part would just be the whole question.
      if (!rows.children.length) { addRow(); }
      addRow();
      rows.lastElementChild.querySelector('input').focus();
    });
    rows.addEventListener('click', function (event) {
      var remove = event.target.closest('[data-remove-part]');
      if (remove) {
        remove.closest('[data-part-row]').remove();
        update();
      }
    });
    rows.addEventListener('input', update);
    update();
  });
})();
