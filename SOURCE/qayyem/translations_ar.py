"""Arabic interface text, keyed by the English it replaces. See i18n.py.

Keys must match the English in the code exactly, markup and entities
included; tests/test_i18n.py fails if one is missing or if a translation
drops a %(placeholder)s.
"""

AR = {
    # --- Layout ---------------------------------------------------------------
    "Qayyem": "قيّم",
    "New grading": "تصحيح جديد",
    "Results": "النتائج",
    "Settings": "الإعدادات",
    "Sign out": "تسجيل الخروج",
    "Sign out and delete": "تسجيل الخروج والحذف",
    "Menu": "القائمة",

    # --- Class overview and student search on the results page --------------
    "Low": "منخفض",
    "High": "مرتفع",
    "below %(low)s%%": "أقل من %(low)s%%",
    "%(low)s–%(high)s%%": "%(low)s–%(high)s%%",
    "%(high)s%% and above": "%(high)s%% فأكثر",
    "Top %(count)s students": "أعلى %(count)s طلاب",
    "Percentage": "النسبة المئوية",
    "Average per question": "المتوسط لكل سؤال",
    "Highest: %(high)s (%(high_pct)s%%) · Lowest: %(low)s (%(low_pct)s%%)":
        "الأعلى: %(high)s (%(high_pct)s%%) · الأدنى: %(low)s (%(low_pct)s%%)",
    "Student groups": "مجموعات الطلاب",
    "%(count)s of %(total)s students": "%(count)s من %(total)s طالبًا",
    "Find a student": "البحث عن طالب",
    "Type a student ID": "اكتب الرقم الجامعي",
    "No student with that ID.": "لا يوجد طالب بهذا الرقم.",
    "Rank %(rank)s of %(total)s": "الترتيب %(rank)s من %(total)s",
    "Download Excel for this student": "تنزيل ملف Excel لهذا الطالب",
    "Highest question": "أعلى سؤال",
    "Student answer": "إجابة الطالب",
    "Answer": "الإجابة",
    "Close": "إغلاق",
    "Switch to light theme": "التبديل إلى الوضع الفاتح",
    "Switch to dark theme": "التبديل إلى الوضع الداكن",
    "Qayyem &mdash; College of Computing &amp; Informatics, Prince Musaid bin Abdulrahman University":
        "قيّم &mdash; كلية الحوسبة والمعلوماتية، جامعة الأمير مساعد بن عبدالرحمن",
    "You have %(count)s graded result set(s) you have not downloaded. Signing out "
    "permanently deletes them. Continue?":
        "لديك %(count)s من مجموعات النتائج المصححة لم تُنزَّل بعد. تسجيل الخروج "
        "يحذفها نهائيًا. هل تريد المتابعة؟",

    # --- Sign in --------------------------------------------------------------
    "Sign in": "تسجيل الدخول",
    "Instructor sign in": "تسجيل دخول عضو هيئة التدريس",
    "Accounts are created by the system administrator.": "يُنشئ مسؤول النظام الحسابات.",
    "Email": "البريد الإلكتروني",
    "Password": "كلمة المرور",
    "Incorrect email or password.": "البريد الإلكتروني أو كلمة المرور غير صحيحة.",
    "Too many failed sign-in attempts. Try again in %(minutes)s minute(s).":
        "محاولات دخول فاشلة كثيرة. حاول مرة أخرى بعد %(minutes)s دقيقة.",
    "Your session expired after inactivity. Please sign in again.":
        "انتهت جلستك بسبب عدم النشاط. يرجى تسجيل الدخول مرة أخرى.",
    "You have been signed out and the student data was deleted.":
        "تم تسجيل خروجك وحُذفت بيانات الطلاب.",
    "You have %(count)s graded result set(s) you have not downloaded, and signing "
    "out deletes them. Download them first, or use “Sign out and delete” to go ahead.":
        "لديك %(count)s من مجموعات النتائج المصححة لم تُنزَّل بعد، وتسجيل الخروج "
        "يحذفها. نزّلها أولًا، أو استخدم «تسجيل الخروج والحذف» للمتابعة.",

    # --- Errors ---------------------------------------------------------------
    "Back to Qayyem": "العودة إلى قيّم",
    "That page does not exist.": "هذه الصفحة غير موجودة.",
    "That upload is larger than 8 MB.": "حجم الملف المرفوع أكبر من 8 ميغابايت.",
    "Something went wrong on the server.": "حدث خطأ في الخادم.",
    "The form expired or did not come from this site. Reload the page and try again.":
        "انتهت صلاحية النموذج أو لم يُرسَل من هذا الموقع. أعد تحميل الصفحة وحاول مرة أخرى.",

    # --- Upload ---------------------------------------------------------------
    "Grade an assignment": "تصحيح واجب",
    "Upload student responses, provide the ideal answer, and Qayyem grades each "
    "response and writes Arabic feedback.":
        "ارفع إجابات الطلاب وأدخل الإجابة النموذجية، وسيصحح قيّم كل إجابة ويكتب "
        "ملاحظات باللغة العربية.",
    "Grading is not set up yet.": "التصحيح غير مُعدّ بعد.",
    "Add a key": "إضافة مفتاح",
    "Grading with <strong>%(provider)s</strong>, using %(source)s.":
        "التصحيح باستخدام <strong>%(provider)s</strong>، عبر %(source)s.",
    "Change": "تغيير",
    "Student responses": "إجابات الطلاب",
    "A .csv or .xlsx file with a student ID column and a response column. English "
    "or Arabic column headings both work":
        "ملف ‎.csv أو ‎.xlsx يحتوي على عمود للرقم الجامعي وعمود للإجابة. تُقبل "
        "عناوين الأعمدة بالعربية أو الإنجليزية",
    "or": "أو",
    "For a whole exam, use one answer column per question (<code>answer 1</code>, "
    "<code>answer 2</code>, &hellip;); you then set each question&#39;s ideal "
    "answer and marks on the next page.":
        "لاختبار كامل، خصص عمود إجابة لكل سؤال (<code>answer 1</code>، "
        "<code>answer 2</code>، &hellip;)؛ ثم تحدد الإجابة النموذجية والدرجة لكل "
        "سؤال في الصفحة التالية.",
    "Ideal answer": "الإجابة النموذجية",
    "The model answer every response is compared against.":
        "الإجابة التي تُقارن بها كل إجابة طالب.",
    "Book or slides": "كتاب أو شرائح",
    "(optional)": "(اختياري)",
    "Grading rubric": "معايير التصحيح",
    "How marks should be awarded. Supplying this measurably improves consistency, "
    "so it is worth a sentence or two.":
        "كيفية توزيع الدرجات. إضافتها تحسّن اتساق التصحيح بشكل ملحوظ، لذا تستحق "
        "جملة أو جملتين.",
    "Maximum score": "الدرجة القصوى",
    "Grade responses": "تصحيح الإجابات",
    "Uploading…": "جارٍ الرفع…",
    "<strong>Student data is not kept.</strong> Responses and grades are deleted "
    "when you sign out or your session expires. Download the Excel file to keep a copy.":
        "<strong>لا تُحفظ بيانات الطلاب.</strong> تُحذف الإجابات والدرجات عند تسجيل "
        "الخروج أو انتهاء الجلسة. نزّل ملف Excel للاحتفاظ بنسخة.",
    "Enter the ideal answer, or upload a book or slides file, that student "
    "responses are compared against.":
        "أدخل الإجابة النموذجية، أو ارفع ملف كتاب أو شرائح، لتُقارن به إجابات الطلاب.",
    "Maximum score must be a number between 0 and 1000.":
        "يجب أن تكون الدرجة القصوى رقمًا بين 0 و1000.",
    "That file is larger than 8 MB.": "حجم هذا الملف أكبر من 8 ميغابايت.",
    "Grading %(count)s response(s). This page updates as it runs.":
        "جارٍ تصحيح %(count)s إجابة. تتحدث هذه الصفحة تلقائيًا أثناء التصحيح.",

    # --- Exam set-up ----------------------------------------------------------
    "Set up questions": "إعداد الأسئلة",
    "This file has %(count)s questions. Give each one its ideal answer and maximum "
    "score, then start grading.":
        "يحتوي هذا الملف على %(count)s أسئلة. أدخل لكل سؤال إجابته النموذجية ودرجته "
        "القصوى، ثم ابدأ التصحيح.",
    "This file has %(count)s questions. Give each one the ideal answer it is "
    "compared against and how many marks it is worth. Questions can be worth "
    "different marks; the exam total is their sum.":
        "يحتوي هذا الملف على %(count)s أسئلة. أدخل لكل سؤال الإجابة النموذجية التي "
        "يُقارن بها وعدد الدرجات المخصصة له. يمكن أن تختلف درجات الأسئلة؛ ومجموع "
        "الاختبار هو مجموع درجاتها.",
    "Marks for this question": "درجة هذا السؤال",
    "Grade all questions": "تصحيح جميع الأسئلة",
    "Exam total:": "مجموع الاختبار:",
    "Question %(number)s (%(title)s): %(error)s": "السؤال %(number)s (%(title)s): %(error)s",
    "Q%(n)s": "س%(n)s",

    # --- Results --------------------------------------------------------------
    "Grading sessions": "جلسات التصحيح",
    "You have not graded anything in this session.": "لم تصحح أي شيء في هذه الجلسة.",
    "File": "الملف",
    "Responses": "الإجابات",
    "Students": "الطلاب",
    "Status": "الحالة",
    "Complete": "مكتمل",
    "Not downloaded": "لم يُنزَّل",
    "Failed": "فشل",
    "Needs setup": "بحاجة إلى إعداد",
    "Grading %(done)s/%(total)s": "جارٍ التصحيح %(done)s/%(total)s",
    "Download Excel": "تنزيل ملف Excel",
    "These are deleted when you sign out or your session expires (data-retention "
    "requirement). Download anything you need to keep.":
        "تُحذف هذه عند تسجيل الخروج أو انتهاء الجلسة (متطلب الاحتفاظ بالبيانات). "
        "نزّل ما تحتاج إلى الاحتفاظ به.",
    "Graded %(when)s &middot; out of %(max)s": "صُحح في %(when)s &middot; من %(max)s",
    "Grading %(done)s of %(total)s&hellip;": "جارٍ تصحيح %(done)s من %(total)s&hellip;",
    "Grading progress": "تقدم التصحيح",
    "You can leave this page open; it updates itself.":
        "يمكنك ترك هذه الصفحة مفتوحة؛ فهي تتحدث تلقائيًا.",
    "Grading failed.": "فشل التصحيح.",
    "An unexpected error occurred.": "حدث خطأ غير متوقع.",
    "Your uploaded responses were kept.": "تم الاحتفاظ بالإجابات المرفوعة.",
    "Graded": "تم تصحيحها",
    "Average": "المتوسط",
    "Needs attention": "تحتاج إلى مراجعة",
    "Student ID": "الرقم الجامعي",
    "Score": "الدرجة",
    "Total": "المجموع",
    "Feedback": "الملاحظات",
    "Awaiting grading&hellip;": "بانتظار التصحيح&hellip;",
    "Grading is not finished yet, so there is nothing to download.":
        "لم ينتهِ التصحيح بعد، لذا لا يوجد ما يمكن تنزيله.",
    # Stored by the grading worker, which has no request to translate for, so
    # these are translated when shown.
    "An unexpected error stopped grading. Your uploaded responses were kept, so "
    "you can try grading again.":
        "أوقف خطأ غير متوقع التصحيح. تم الاحتفاظ بالإجابات المرفوعة، لذا يمكنك "
        "إعادة المحاولة.",
    "Not graded: provider rate limit reached": "لم تُصحح: بلغ مزود الخدمة حد الطلبات",

    # --- File parsing ---------------------------------------------------------
    "No file was selected.": "لم يتم اختيار ملف.",
    "Only .csv and .xlsx files are supported. You uploaded '%(name)s'.":
        "تُدعم ملفات ‎.csv و‎.xlsx فقط. لقد رفعت '%(name)s'.",
    "That file is empty.": "هذا الملف فارغ.",
    "That file has no rows of data.": "لا يحتوي هذا الملف على صفوف بيانات.",
    "That .xlsx file could not be read. Re-save it from Excel and try again. (%(detail)s)":
        "تعذرت قراءة ملف ‎.xlsx هذا. احفظه مرة أخرى من Excel وحاول مجددًا. (%(detail)s)",
    "That CSV file could not be read. Check it opens in Excel. (%(detail)s)":
        "تعذرت قراءة ملف CSV هذا. تأكد من أنه يُفتح في Excel. (%(detail)s)",
    "The file's text encoding could not be determined. Save it as CSV UTF-8 and "
    "try again. (%(detail)s)":
        "تعذر تحديد ترميز نص الملف. احفظه بصيغة CSV UTF-8 وحاول مرة أخرى. (%(detail)s)",
    "Could not find a student ID column. Found these columns: %(found)s. Name them "
    "'student_id' and 'response' (or the Arabic equivalents) and try again.":
        "تعذر العثور على عمود الرقم الجامعي. الأعمدة الموجودة: %(found)s. سمِّ "
        "الأعمدة 'student_id' و'response' (أو ما يقابلها بالعربية) وحاول مرة أخرى.",
    "Could not find a response column. Found these columns: %(found)s. Name them "
    "'student_id' and 'response' (or the Arabic equivalents) and try again.":
        "تعذر العثور على عمود الإجابة. الأعمدة الموجودة: %(found)s. سمِّ الأعمدة "
        "'student_id' و'response' (أو ما يقابلها بالعربية) وحاول مرة أخرى.",
    "More than one column is named like the answer column (%(columns)s). Rename "
    "all but one.":
        "يوجد أكثر من عمود يحمل اسم عمود الإجابة (%(columns)s). غيّر أسماءها جميعًا "
        "عدا واحدًا.",
    "This file looks like it holds more than one question: %(count)s columns could "
    "be answers (%(columns)s). Qayyem grades one question at a time, because each "
    "question needs its own ideal answer and rubric. Upload one question per file, "
    "or rename just the column you want graded to 'response'.":
        "يبدو أن هذا الملف يحتوي على أكثر من سؤال: %(count)s أعمدة قد تكون إجابات "
        "(%(columns)s). يصحح قيّم سؤالًا واحدًا في كل مرة، لأن لكل سؤال إجابته "
        "النموذجية ومعاييره. ارفع سؤالًا واحدًا في كل ملف، أو غيّر اسم العمود "
        "المراد تصحيحه فقط إلى 'response'.",
    "That file has %(rows)s rows, above the limit of %(limit)s. Split it into "
    "smaller files.":
        "يحتوي هذا الملف على %(rows)s صفًا، وهذا يتجاوز الحد البالغ %(limit)s. "
        "قسّمه إلى ملفات أصغر.",
    "That file has %(count)s answer columns, above the limit of %(limit)s "
    "questions. Split it into smaller files.":
        "يحتوي هذا الملف على %(count)s عمود إجابة، وهذا يتجاوز الحد البالغ "
        "%(limit)s سؤالًا. قسّمه إلى ملفات أصغر.",
    "The student ID and response columns resolved to the same column "
    "('%(column)s'). Rename one of them.":
        "عمود الرقم الجامعي وعمود الإجابة يشيران إلى العمود نفسه ('%(column)s'). "
        "غيّر اسم أحدهما.",
    "Row %(row)s has a response but no student ID.":
        "الصف %(row)s يحتوي على إجابة دون رقم جامعي.",
    "Student ID '%(id)s' appears twice (rows %(first)s and %(second)s). Each "
    "student must appear once.":
        "الرقم الجامعي '%(id)s' مكرر (الصفان %(first)s و%(second)s). يجب أن يظهر "
        "كل طالب مرة واحدة.",
    "No student responses were found in that file.":
        "لم يُعثر على إجابات طلاب في هذا الملف.",

    # --- Book or slides files -------------------------------------------------
    "The reference text file's encoding could not be read. Save it as UTF-8.":
        "تعذرت قراءة ترميز الملف النصي المرجعي. احفظه بترميز UTF-8.",
    "Reference material must be a .pdf, .pptx, .docx or .txt file. You uploaded "
    "'%(name)s'.":
        "يجب أن تكون المادة المرجعية ملف ‎.pdf أو ‎.pptx أو ‎.docx أو ‎.txt. لقد "
        "رفعت '%(name)s'.",
    "The reference material file is empty.": "ملف المادة المرجعية فارغ.",
    "'%(name)s' could not be read. Re-save it and try again. (%(detail)s)":
        "تعذرت قراءة '%(name)s'. احفظه مرة أخرى وحاول مجددًا. (%(detail)s)",
    "No text was found in '%(name)s'. If it is a scanned PDF, paste the answer "
    "into the box instead.":
        "لم يُعثر على نص في '%(name)s'. إذا كان ملف PDF ممسوحًا ضوئيًا، فالصق "
        "الإجابة في المربع بدلًا من ذلك.",

    # --- Settings -------------------------------------------------------------
    "Grading settings": "إعدادات التصحيح",
    "Choose which AI service grades your assignments, and use your own account "
    "if you prefer.":
        "اختر خدمة الذكاء الاصطناعي التي تصحح واجباتك، واستخدم حسابك الخاص إن رغبت.",
    "A key is stored but cannot be read, which happens when the server&#39;s "
    "<code>SECRET_KEY</code> changes after a key is saved. Enter your key again.":
        "يوجد مفتاح محفوظ لكن تتعذر قراءته، ويحدث ذلك عند تغيير "
        "<code>SECRET_KEY</code> في الخادم بعد حفظ المفتاح. أدخل مفتاحك مرة أخرى.",
    "AI provider": "مزود الذكاء الاصطناعي",
    "Model": "النموذج",
    "Ask your provider which models this key can use":
        "اسأل المزود عن النماذج التي يمكن لهذا المفتاح استخدامها",
    "Refresh": "تحديث",
    "Type a model name": "اكتب اسم النموذج",
    "Other (type a name)…": "آخر (اكتب الاسم)…",
    "Showing the models your key can actually use.":
        "تُعرض النماذج التي يستطيع مفتاحك استخدامها فعليًا.",
    "Common choices shown. Press <strong>Refresh</strong> to list the models your "
    "own key can use &mdash; that way a mistyped name cannot fail halfway through "
    "grading a class.":
        "تُعرض الخيارات الشائعة. اضغط <strong>تحديث</strong> لعرض النماذج التي "
        "يستطيع مفتاحك استخدامها &mdash; حتى لا يتسبب اسم مكتوب خطأً في توقف "
        "التصحيح في منتصفه.",
    "Your API key": "مفتاح API الخاص بك",
    "Currently using your own key:": "تستخدم حاليًا مفتاحك الخاص:",
    "No key of your own. Grading uses the key this server was set up with.":
        "لا يوجد مفتاح خاص بك. يستخدم التصحيح المفتاح المُعدّ في الخادم.",
    "No key is set here and the server has none either, so grading will fail "
    "until you add one.":
        "لا يوجد مفتاح هنا ولا في الخادم، لذا سيفشل التصحيح حتى تضيف مفتاحًا.",
    "Leave blank to keep your saved key": "اتركه فارغًا للإبقاء على مفتاحك المحفوظ",
    "Paste your key": "الصق مفتاحك",
    "Stored encrypted and never shown again. Gemini keys come from "
    "<a href=\"https://aistudio.google.com/apikey\" target=\"_blank\" "
    "rel=\"noopener\">Google AI Studio</a> (free); OpenAI keys from "
    "<a href=\"https://platform.openai.com/api-keys\" target=\"_blank\" "
    "rel=\"noopener\">platform.openai.com</a> (paid).":
        "يُحفظ مشفرًا ولا يُعرض مرة أخرى. تحصل على مفاتيح Gemini من "
        "<a href=\"https://aistudio.google.com/apikey\" target=\"_blank\" "
        "rel=\"noopener\">Google AI Studio</a> (مجانًا)، ومفاتيح OpenAI من "
        "<a href=\"https://platform.openai.com/api-keys\" target=\"_blank\" "
        "rel=\"noopener\">platform.openai.com</a> (مدفوعة).",
    "Save settings": "حفظ الإعدادات",
    "Remove your saved API key? Grading will fall back to the server key.":
        "هل تريد حذف مفتاح API المحفوظ؟ سيعود التصحيح إلى استخدام مفتاح الخادم.",
    "Remove my key": "حذف مفتاحي",
    "Test connection": "اختبار الاتصال",
    "Grades one sample answer so you find problems now, not halfway through a class.":
        "يصحح إجابة تجريبية واحدة لتكتشف المشكلات الآن، لا في منتصف تصحيح الشعبة.",
    "<strong>Your key is yours.</strong> It is encrypted before being saved and is "
    "never sent back to this page or included in any export. Usage is billed to "
    "whichever account the key belongs to.":
        "<strong>مفتاحك ملكك.</strong> يُشفَّر قبل حفظه، ولا يُعاد إلى هذه الصفحة "
        "ولا يُضمَّن في أي ملف مُصدَّر. تُحتسب تكلفة الاستخدام على الحساب الذي يتبعه "
        "المفتاح.",
    "Settings saved.": "تم حفظ الإعدادات.",
    "Your API key was removed. Grading will use the server's key.":
        "تم حذف مفتاح API الخاص بك. سيستخدم التصحيح مفتاح الخادم.",
    "Choose a provider from the list.": "اختر مزودًا من القائمة.",
    "Could not fetch the model list: %(detail)s": "تعذر جلب قائمة النماذج: %(detail)s",
    "Found %(count)s model(s) your key can use.":
        "تم العثور على %(count)s نموذج يستطيع مفتاحك استخدامه.",
    "That key returned no usable grading models.":
        "لم يُرجع هذا المفتاح أي نماذج صالحة للتصحيح.",
    "Configuration problem: %(detail)s": "مشكلة في الإعداد: %(detail)s",
    "Could not reach the provider: %(detail)s": "تعذر الوصول إلى المزود: %(detail)s",
    "Test failed: %(detail)s": "فشل الاختبار: %(detail)s",
    "Connection works. %(model)s returned a score of %(score)s and Arabic feedback.":
        "الاتصال يعمل. أعاد %(model)s درجة %(score)s مع ملاحظات بالعربية.",
    "no result returned": "لم تُرجع أي نتيجة",
    "The provider responded, but the reply was unusable: %(detail)s":
        "استجاب المزود، لكن الرد غير صالح للاستخدام: %(detail)s",

    # Grading readiness, shown on the upload page.
    "the offline test grader (no AI, for testing only)":
        "المصحح التجريبي دون اتصال (بلا ذكاء اصطناعي، للاختبار فقط)",
    "no key -- it scores by word overlap": "دون مفتاح -- يمنح الدرجة حسب تطابق الكلمات",
    "your own key": "مفتاحك الخاص",
    "the key this server is configured with": "المفتاح المُعدّ في هذا الخادم",
    "No API key is available for %(provider)s, so grading cannot run yet.":
        "لا يتوفر مفتاح API لـ %(provider)s، لذا لا يمكن بدء التصحيح بعد.",
    "Free tier: a large class may reach the request limit and stop part way. Your "
    "responses are kept, so you can grade again once the limit resets.":
        "الفئة المجانية: قد تبلغ الشعبة الكبيرة حد الطلبات فيتوقف التصحيح في "
        "منتصفه. تُحفظ الإجابات، لذا يمكنك إعادة التصحيح بعد إعادة ضبط الحد.",
    "Usage is charged to the OpenAI account this key belongs to.":
        "تُحتسب تكلفة الاستخدام على حساب OpenAI الذي يتبعه هذا المفتاح.",
    "Usage is charged to the Anthropic account this key belongs to.":
        "تُحتسب تكلفة الاستخدام على حساب Anthropic الذي يتبعه هذا المفتاح.",
    "Usage is charged to the DeepSeek account this key belongs to, and requests "
    "are processed on servers in China.":
        "تُحتسب تكلفة الاستخدام على حساب DeepSeek الذي يتبعه هذا المفتاح، وتُعالج "
        "الطلبات على خوادم في الصين.",

    # Provider descriptions (grading/factory.py), shown through |translate.
    "Free tier available. No payment card needed.": "تتوفر فئة مجانية. لا حاجة إلى بطاقة دفع.",
    "The free tier limits how many requests you may send per minute and per day. "
    "Grading a large class can reach that limit and stop part way through. If it "
    "does, your uploaded responses are kept and you can grade again once the limit "
    "resets.":
        "تحدد الفئة المجانية عدد الطلبات المسموح بها في الدقيقة وفي اليوم. قد يبلغ "
        "تصحيح شعبة كبيرة هذا الحد فيتوقف في منتصفه. عندها تُحفظ الإجابات المرفوعة "
        "ويمكنك إعادة التصحيح بعد إعادة ضبط الحد.",
    "Requires a paid OpenAI account with billing enabled.":
        "يتطلب حساب OpenAI مدفوعًا مع تفعيل الفوترة.",
    "Usage is charged to your own OpenAI account. Short answers cost very little, "
    "but the cost is yours and rises with the number of students.":
        "تُحتسب تكلفة الاستخدام على حسابك في OpenAI. تكلفة الإجابات القصيرة زهيدة، "
        "لكنها على حسابك وتزداد بزيادة عدد الطلاب.",
    "Requires a paid Anthropic account.": "يتطلب حساب Anthropic مدفوعًا.",
    "Usage is charged to your own Anthropic account. Claude handles Arabic well, "
    "but it has no free tier, so every graded class costs money.":
        "تُحتسب تكلفة الاستخدام على حسابك في Anthropic. يتعامل Claude مع العربية "
        "جيدًا، لكن لا توجد فئة مجانية، لذا فلكل شعبة تُصحح تكلفة.",
    "Paid, but among the cheapest options.": "مدفوع، لكنه من أرخص الخيارات.",
    "Usage is charged to your own DeepSeek account. It is inexpensive, but note "
    "that requests are processed on servers in China -- check that your university "
    "permits sending student work there before using it.":
        "تُحتسب تكلفة الاستخدام على حسابك في DeepSeek. تكلفته منخفضة، لكن لاحظ أن "
        "الطلبات تُعالج على خوادم في الصين -- تأكد من أن جامعتك تسمح بإرسال أعمال "
        "الطلاب إليها قبل استخدامه.",

    # --- Ideal answer source and marking in parts -----------------------------
    "Ideal answer source": "مصدر الإجابة النموذجية",
    "Typed answer": "إجابة مكتوبة",
    "Both": "كلاهما",
    "A textbook chapter or lecture slides (.pdf, .pptx, .docx or .txt). Upload "
    "only the relevant pages; long files are trimmed.":
        "فصل من كتاب أو شرائح محاضرة (‎.pdf أو ‎.pptx أو ‎.docx أو ‎.txt). ارفع "
        "الصفحات ذات الصلة فقط؛ تُختصر الملفات الطويلة.",
    "Upload only the pages this question covers; long files are trimmed.":
        "ارفع الصفحات التي يغطيها هذا السؤال فقط؛ تُختصر الملفات الطويلة.",
    "Choose a book or slides file to use as the ideal answer.":
        "اختر ملف كتاب أو شرائح لاستخدامه إجابةً نموذجية.",
    "You chose both: type the ideal answer and choose a book or slides file.":
        "اخترت كليهما: اكتب الإجابة النموذجية واختر ملف كتاب أو شرائح.",
    "Marks split into parts": "توزيع الدرجة على أجزاء",
    "For a question marked in parts, e.g. 4 marks for the definition and 6 for "
    "an example. Each part is scored separately and the maximum score becomes "
    "their sum.":
        "للسؤال الذي تُوزَّع درجته على أجزاء، مثل 4 درجات للتعريف و6 للمثال. "
        "يُقيَّم كل جزء على حدة، وتصبح الدرجة القصوى مجموعها.",
    "Add part": "إضافة جزء",
    "Part, e.g. Definition": "الجزء، مثل: التعريف",
    "Part name": "اسم الجزء",
    "Marks": "الدرجة",
    "Remove part": "حذف الجزء",
    "Split the marks into at least two parts, or remove the part.":
        "وزّع الدرجة على جزأين على الأقل، أو احذف الجزء.",
    "A question can have at most %(count)s parts.":
        "يمكن أن يحتوي السؤال على %(count)s أجزاء كحد أقصى.",
    "Each part needs a name and marks greater than 0.":
        "يحتاج كل جزء إلى اسم ودرجة أكبر من 0.",
    "Model returned no per-part scores": "لم يُرجع النموذج درجات الأجزاء",

    # --- Sign up --------------------------------------------------------------
    "Sign up": "إنشاء حساب",
    "Create an account": "إنشاء حساب",
    "Create account": "إنشاء الحساب",
    "New to Qayyem?": "جديد في قيّم؟",
    "Already have an account?": "لديك حساب بالفعل؟",
    "Sign in to grade answers and manage your subjects.":
        "سجّل الدخول لتصحيح الإجابات وإدارة موادك.",
    "For instructors. Your subjects and question banks are kept with your account; "
    "student answers are deleted when you sign out.":
        "لأعضاء هيئة التدريس. تُحفظ موادك وبنوك أسئلتك في حسابك، "
        "وتُحذف إجابات الطلاب عند تسجيل الخروج.",
    "Full name": "الاسم الكامل",
    "Confirm password": "تأكيد كلمة المرور",
    "At least 8 characters.": "8 أحرف على الأقل.",
    "Use your university email (%(domains)s).": "استخدم بريدك الجامعي (%(domains)s).",
    "Enter your full name.": "أدخل اسمك الكامل.",
    "Enter a valid email address.": "أدخل بريدًا إلكترونيًا صحيحًا.",
    "Sign up with your university email (%(domains)s).":
        "أنشئ الحساب ببريدك الجامعي (%(domains)s).",
    "The password must be at least %(count)s characters.":
        "يجب ألا تقل كلمة المرور عن %(count)s أحرف.",
    "The two passwords do not match.": "كلمتا المرور غير متطابقتين.",
    "Too many attempts. Try again later.": "محاولات كثيرة. حاول مرة أخرى لاحقًا.",
    "An account already exists for that email. Sign in instead.":
        "يوجد حساب بهذا البريد بالفعل. سجّل الدخول بدلًا من ذلك.",
    "Welcome to Qayyem, %(name)s. Your account is ready.":
        "مرحبًا بك في قيّم يا %(name)s. حسابك جاهز.",

    # --- Subjects -------------------------------------------------------------
    "Subjects": "المواد",
    "Subject": "المادة",
    "No subject": "بدون مادة",
    "Each subject keeps its own questions, model answers, marks and grading guidelines.":
        "لكل مادة أسئلتها وإجاباتها النموذجية ودرجاتها وإرشادات تصحيحها الخاصة.",
    "%(count)s question(s) &middot; %(marks)s marks": "%(count)s سؤال &middot; %(marks)s درجة",
    "Add a subject": "إضافة مادة",
    "Subject name": "اسم المادة",
    "Course code": "رمز المقرر",
    "e.g. Operating Systems": "مثل: نظم التشغيل",
    "e.g. IT241": "مثل: IT241",
    "Create subject": "إنشاء المادة",
    "Give the subject a name.": "اكتب اسم المادة.",
    "You can have at most %(count)s subjects.": "يمكنك إضافة %(count)s مادة كحد أقصى.",
    "Subject “%(name)s” created. Add its questions, or import them from Word.":
        "أُنشئت مادة «%(name)s». أضف أسئلتها، أو استوردها من ملف وورد.",
    "Subject saved.": "حُفظت المادة.",
    "Subject “%(name)s” and its question bank were deleted.":
        "حُذفت مادة «%(name)s» وبنك أسئلتها.",
    "Grade student answers": "تصحيح إجابات الطلاب",
    "Download questions (Excel)": "تنزيل الأسئلة (إكسل)",
    "Import questions from Word": "استيراد الأسئلة من وورد",
    "Upload the exam as you wrote it. The AI takes only the questions from it, with "
    "their choices, answers and marks, skipping the cover page, instructions and "
    "anything else; mark the correct choice or write the model answer in the file so "
    "it is copied too. You can review the questions here and download them as Excel.":
        "ارفع الاختبار كما كتبته. يأخذ الذكاء الاصطناعي الأسئلة وحدها بخياراتها "
        "وإجاباتها ودرجاتها، ويتجاوز صفحة الغلاف والتعليمات وكل ما سواها؛ حدّد الخيار "
        "الصحيح أو اكتب الإجابة النموذجية في الملف لتُنقل معها. تراجع الأسئلة هنا "
        "وتنزّلها ملف إكسل.",
    "Word file": "ملف وورد",
    "Existing questions": "الأسئلة الحالية",
    "Add to the existing questions": "إضافتها إلى الأسئلة الحالية",
    "Replace the existing questions": "استبدال الأسئلة الحالية",
    "Import": "استيراد",
    "Without an AI provider, how should the Word file look?":
        "دون مزوّد ذكاء اصطناعي، كيف يكون شكل ملف وورد؟",
    "Add from a Word file": "إضافة من ملف وورد",
    "The AI reads the file and takes only the questions from it, with their choices, "
    "answers and marks, skipping the cover page, instructions and anything else. They "
    "are added to this subject&#39;s questions, where you can check and edit them.":
        "يقرأ الذكاء الاصطناعي الملف ويأخذ منه الأسئلة وحدها بخياراتها وإجاباتها "
        "ودرجاتها، ويتجاوز صفحة الغلاف والتعليمات وكل ما سواها. تُضاف إلى أسئلة هذه "
        "المادة، حيث تراجعها وتعدّلها.",
    "Read questions": "قراءة الأسئلة",
    "or type one question": "أو اكتب سؤالًا واحدًا",
    "Reading the file…": "جارٍ قراءة الملف…",
    "No questions were found in '%(name)s'.": "لم يُعثر على أسئلة في '%(name)s'.",
    "The Word file is long, so only its first part was read. Check that the last "
    "questions were imported.":
        "ملف وورد طويل، فقُرئ جزؤه الأول فقط. تأكد من استيراد الأسئلة الأخيرة.",
    "No AI provider is set up on the Settings page, so the questions were read by "
    "their numbering instead.":
        "لم يُضبط مزوّد ذكاء اصطناعي في صفحة الإعدادات، فقُرئت الأسئلة حسب ترقيمها.",
    "The AI could not read the file (%(error)s), so the questions were read by their "
    "numbering instead.":
        "تعذّر على الذكاء الاصطناعي قراءة الملف (%(error)s)، فقُرئت الأسئلة حسب ترقيمها.",
    "Word&#39;s automatic numbering works too. Marks in brackets after a question are "
    "picked up; otherwise a choice question gets 1 mark and a written one 5, and you "
    "can change them below.":
        "الترقيم التلقائي في وورد يعمل أيضًا. تُقرأ الدرجة المكتوبة بين قوسين بعد السؤال، "
        "وإلا يأخذ سؤال الاختيار درجة واحدة والسؤال المقالي 5 درجات، ويمكنك تغييرها أدناه.",
    "Subject settings": "إعدادات المادة",
    "Grading guidelines": "إرشادات التصحيح",
    "e.g. Accept answers in Arabic or English. Deduct for missing key terms.":
        "مثل: تُقبل الإجابة بالعربية أو الإنجليزية. تُخصم درجة عند غياب المصطلحات الأساسية.",
    "Applied to every question of this subject, on top of each question&#39;s own rubric.":
        "تُطبَّق على كل أسئلة هذه المادة، إضافةً إلى معايير كل سؤال.",
    "Save": "حفظ",
    "Delete this subject and all its questions?": "هل تريد حذف هذه المادة وكل أسئلتها؟",
    "Delete subject": "حذف المادة",
    "Question bank": "بنك الأسئلة",
    "Add question": "إضافة سؤال",
    "No questions yet. Import the exam from Word, or add questions one by one.":
        "لا توجد أسئلة بعد. استورد الاختبار من وورد، أو أضف الأسئلة واحدًا تلو الآخر.",
    "Multiple choice": "اختيار من متعدد",
    "MSQ": "سؤال اختيار متعدد",
    "Open question": "سؤال مفتوح",
    "All": "الكل",
    "Filter question bank by type": "تصفية بنك الأسئلة حسب النوع",
    "No %(type)s questions in this exam yet.": "لا توجد أسئلة من نوع %(type)s في هذا الاختبار بعد.",
    "Written": "مقالي",
    "%(marks)s mark(s)": "%(marks)s درجة",
    "Correct answer": "الإجابة الصحيحة",
    "No choice is starred as correct yet.": "لم يُحدَّد الخيار الصحيح بنجمة بعد.",
    "No model answer yet. Add one before grading this question.":
        "لا توجد إجابة نموذجية بعد. أضفها قبل تصحيح هذا السؤال.",
    "Parts:": "الأجزاء:",
    "Rubric:": "المعايير:",
    "Edit": "تعديل",
    "Grade answers to this question": "تصحيح إجابات هذا السؤال",
    "Delete this question?": "هل تريد حذف هذا السؤال؟",
    "Delete": "حذف",
    "Grading sessions for this subject": "جلسات التصحيح لهذه المادة",
    "%(count)s response(s)": "%(count)s إجابة",
    "Choose the Word file with the questions.": "اختر ملف وورد الذي يحتوي على الأسئلة.",
    "Imported %(count)s question(s) from “%(name)s”. Check them below.":
        "استُورد %(count)s سؤال من «%(name)s». راجعها أدناه.",

    # --- One bank question ----------------------------------------------------
    "Edit question": "تعديل السؤال",
    "Question %(n)s": "السؤال %(n)s",
    "Question": "السؤال",
    "Question type": "نوع السؤال",
    "Choices": "الخيارات",
    "One choice per line. Put a star (*) after the correct one.":
        "خيار في كل سطر. ضع نجمة (*) بعد الخيار الصحيح.",
    "One choice per line. Put a star (*) after every correct choice.":
        "خيار في كل سطر. ضع نجمة (*) بعد كل خيار صحيح.",
    "The AI automatically classifies each imported question as MSQ or open question.":
        "يصنّف الذكاء الاصطناعي تلقائياً كل سؤال مستورد كسؤال اختيار متعدد أو سؤال مفتوح.",
    "Model answer": "الإجابة النموذجية",
    "The answer student responses are compared against.":
        "الإجابة التي تُقارن بها إجابات الطلاب.",
    "Save question": "حفظ السؤال",
    "Cancel": "إلغاء",
    "Type the question.": "اكتب السؤال.",
    "A multiple-choice question needs at least two choices, one per line.":
        "يحتاج سؤال الاختيار من متعدد إلى خيارين على الأقل، خيار في كل سطر.",
    "Put a star (*) after the correct choice.": "ضع نجمة (*) بعد الخيار الصحيح.",
    "Question added.": "أُضيف السؤال.",
    "Question saved.": "حُفظ السؤال.",
    "Question deleted.": "حُذف السؤال.",

    # --- Reading questions from Word -----------------------------------------
    "That file could not be read as a Word document. Save it as .docx and try again.":
        "تعذّرت قراءة الملف كمستند وورد. احفظه بصيغة ‎.docx‎ وحاول مرة أخرى.",
    "Questions must be a Word file (.docx). You uploaded '%(name)s'.":
        "يجب أن تكون الأسئلة في ملف وورد (‎.docx‎). رفعت الملف '%(name)s'.",
    "The Word file is empty.": "ملف وورد فارغ.",
    "No questions were found in '%(name)s'. Number each question (1. 2. 3.), put a "
    "letter before each choice (a) b) c)), and mark the correct choice or the model "
    "answer with a star (*).":
        "لم يُعثر على أسئلة في '%(name)s'. رقّم كل سؤال (1. 2. 3.)، وضع حرفًا قبل كل "
        "خيار (أ- ب- ج-)، وحدّد الخيار الصحيح أو الإجابة النموذجية بنجمة (*).",
    "A Word file can hold at most %(count)s questions.":
        "يمكن أن يحتوي ملف وورد على %(count)s سؤال كحد أقصى.",
    "Question %(number)s has choices but none is starred.":
        "السؤال %(number)s له خيارات لكن لم يُحدَّد أي منها بنجمة.",
    "Question %(number)s has no model answer.": "السؤال %(number)s بلا إجابة نموذجية.",

    # --- Upload with a subject ------------------------------------------------
    "Question from the bank": "سؤال من البنك",
    "Answer taken from the question bank": "الإجابة مأخوذة من بنك الأسئلة",
    "Its saved answer, rubric and marks are filled in below. Edit them if needed; changes are saved back to the bank.":
        "عُبّئت إجابته المحفوظة ومعيار تصحيحه ودرجاته أدناه. عدّلها إن لزم، وتُحفظ التعديلات في البنك.",
    "Take the answer from the question bank?": "هل تريد أخذ الإجابة من بنك الأسئلة؟",
    "Pick a saved question of %(subject)s · %(exam)s, and its answer, rubric and marks are filled in for you. Or type the answer below.":
        "اختر سؤالاً محفوظاً من %(subject)s · %(exam)s، وستُعبّأ إجابته ومعيار تصحيحه ودرجاته. أو اكتب الإجابة أدناه.",
    "None, type the answer below": "لا، سأكتب الإجابة أدناه",
    "(no saved answer yet)": "(لا توجد إجابة محفوظة بعد)",
    "Question taken from the question bank": "السؤال مأخوذ من بنك الأسئلة",
    "This question has no saved answer yet. Type it below, and it is saved to the bank for next time.":
        "لا توجد إجابة محفوظة لهذا السؤال بعد. اكتبها أدناه، وستُحفظ في البنك لتستخدمها لاحقاً.",
    "Type the answer below, and it is saved to the %(subject)s question bank for next time.":
        "اكتب الإجابة أدناه، وستُحفظ في بنك أسئلة %(subject)s لتستخدمها لاحقاً.",
    "Choose a subject at the top of the page, then pick one of its saved questions, and its answer, rubric and marks are filled in for you. Or type the answer below.":
        "اختر مادة في أعلى الصفحة، ثم اختر أحد أسئلتها المحفوظة، وستُعبّأ إجابته ومعيار تصحيحه ودرجاته. أو اكتب الإجابة أدناه.",
    "Subjects keep your questions and model answers so you do not retype them.":
        "تحفظ المواد أسئلتك وإجاباتها النموذجية فلا تعيد كتابتها.",
    "This subject has no questions yet.": "لا توجد أسئلة لهذه المادة بعد.",
    "Add or import them": "أضفها أو استوردها",
    "From the %(subject)s question bank:": "من بنك أسئلة %(subject)s:",
    "Question format": "نمط الأسئلة",
    "Single question": "سؤال واحد",
    "Multiple questions": "عدة أسئلة",
    "Choose one question per student, or a whole exam with several questions.":
        "اختر سؤالاً واحداً لكل طالب، أو اختباراً كاملاً يضم عدة أسئلة.",
    "For a whole exam, Qayyem sets up a separate model answer and score for each question on the next step.":
        "في الاختبار الكامل، يتيح قيّم إعداد إجابة نموذجية ودرجة مستقلة لكل سؤال في الخطوة التالية.",
    "It matches questions to the selected exam in your question bank by order.":
        "يطابق الأسئلة مع الاختبار المحدد في بنك أسئلتك حسب ترتيبها.",
    "Continue to question setup": "المتابعة لإعداد الأسئلة",
    "Choose single question or multiple questions.": "اختر سؤالاً واحداً أو عدة أسئلة.",
    "This upload contains multiple questions. Choose Multiple questions, or upload a single-question file.":
        "يحتوي الملف المرفوع على عدة أسئلة. اختر «عدة أسئلة» أو ارفع ملفاً يحتوي على سؤال واحد.",
    "Only one question was found. Choose Single question, or upload an exam with at least two questions.":
        "تم العثور على سؤال واحد فقط. اختر «سؤال واحد» أو ارفع اختباراً يحتوي على سؤالين على الأقل.",
    "Questions in this upload": "الأسئلة في هذا الرفع",
    "One question": "سؤال واحد",
    "Students in this upload": "الطلاب في هذا الرفع",
    "One student": "طالب واحد",
    "Multiple students": "عدة طلاب",
    "For one student, upload one response file. For multiple students, upload a class list or several answer papers.":
        "لطالب واحد، ارفع ملف إجابة واحداً. ولعدة طلاب، ارفع قائمة الصف أو عدة ملفات إجابة.",
    "Two kinds of file work:": "يمكن رفع نوعين من الملفات:",
    "Question text": "نص السؤال",
    "This question and its answer details will be saved to %(subject)s question bank automatically. If blank, the detected question label from the uploaded file will be used.":
        "سيُحفظ هذا السؤال وتفاصيل إجابته تلقائياً في بنك أسئلة مادة %(subject)s. إذا تُرك النص فارغاً، فسيُستخدم عنوان السؤال المستخرج من الملف المرفوع.",
    "Select a subject above if you want to save this question to your question bank.":
        "اختر مادة أعلاه إذا أردت حفظ هذا السؤال في بنك أسئلتك.",
    "Answers will be taken from the question bank": "ستُؤخذ الإجابات من بنك الأسئلة",
    "The saved questions of %(subject)s · %(exam)s (%(count)s) fill questions 1, 2, 3… in order, with their answers, rubrics and marks. You can review and edit them on the next step; changes are saved back to the bank.":
        "تُملأ الأسئلة 1 و2 و3… بالترتيب من الأسئلة المحفوظة في %(subject)s · %(exam)s (%(count)s)، مع إجاباتها ومعايير تصحيحها ودرجاتها. يمكنك مراجعتها وتعديلها في الخطوة التالية، وتُحفظ التعديلات في البنك.",
    "No saved questions for this exam yet": "لا توجد أسئلة محفوظة لهذا الاختبار بعد",
    "Set up each question on the next step, and they are saved to the %(subject)s question bank for next time.":
        "أعدّ كل سؤال في الخطوة التالية، وستُحفظ الأسئلة في بنك أسئلة %(subject)s لتستخدمها لاحقاً.",
    "Take the answers from the question bank?": "هل تريد أخذ الإجابات من بنك الأسئلة؟",
    "Choose a subject and exam at the top of the page, and each question’s saved answer, rubric and marks are filled in for you. Or continue without one and type them on the next step.":
        "اختر المادة والاختبار في أعلى الصفحة، وستُملأ لكل سؤال إجابته المحفوظة ومعيار تصحيحه ودرجاته. أو تابع دون مادة واكتبها في الخطوة التالية.",
    "Choose a subject": "اختر مادة",
    "Choose one student or multiple students.": "اختر طالباً واحداً أو عدة طلاب.",
    "This upload contains %(count)s students. Choose Multiple students, or upload one student's responses.":
        "يحتوي هذا الرفع على %(count)s طالباً. اختر «عدة طلاب» أو ارفع إجابات طالب واحد.",
    "Only one student was found. Choose One student, or upload responses for at least two students.":
        "تم العثور على طالب واحد فقط. اختر «طالب واحد» أو ارفع إجابات طالبين على الأقل.",
    "Added this question to the %(subject)s question bank.":
        "أُضيف هذا السؤال إلى بنك أسئلة مادة %(subject)s.",
    "Saved this question to the %(subject)s question bank.":
        "حُفظ هذا السؤال في بنك أسئلة مادة %(subject)s.",
    "Question text (saved to question bank)": "نص السؤال (يُحفظ في بنك الأسئلة)",
    "Check that this is the full question, not just an answer-column heading.":
        "تأكد من أن هذا هو نص السؤال كاملاً، وليس عنوان عمود الإجابة فقط.",
    "Qayyem loads saved answers, rubrics, marks, and parts from the %(subject)s question bank by question order when available. New questions and your edits are saved back automatically when you start grading.":
        "يحمّل قيّم الإجابات ومعايير التصحيح والدرجات والأجزاء المحفوظة من بنك أسئلة مادة %(subject)s حسب ترتيب الأسئلة عند توفرها. تُحفظ الأسئلة الجديدة وتعديلاتك تلقائياً عند بدء التصحيح.",
    "No subject is selected, so these questions will not be saved to a question bank.":
        "لم تُحدد مادة، لذلك لن تُحفظ هذه الأسئلة في بنك الأسئلة.",
    "Saved the reviewed questions to the %(subject)s question bank.":
        "حُفظت الأسئلة التي راجعتها في بنك أسئلة مادة %(subject)s.",

    # --- Reviewing grades -----------------------------------------------------
    "Review": "مراجعة",
    "Reviewed": "رُوجعت",
    "%(count)s reviewed": "رُوجعت %(count)s",
    "AI score: %(score)s": "درجة الذكاء الاصطناعي: %(score)s",
    "Student&#39;s answer": "إجابة الطالب",
    "Feedback to the student": "التغذية الراجعة للطالب",
    "Save grade": "حفظ الدرجة",
    "Check the grades here before downloading: press <strong>Review</strong> on any "
    "answer to read it and change its score or feedback.":
        "راجع الدرجات هنا قبل التنزيل: اضغط <strong>مراجعة</strong> على أي إجابة "
        "لقراءتها وتعديل درجتها أو التغذية الراجعة.",
    "Wait for grading to finish before changing grades.":
        "انتظر حتى ينتهي التصحيح قبل تعديل الدرجات.",
    "Each part's score must be between 0 and its marks.":
        "يجب أن تكون درجة كل جزء بين 0 ودرجته الكاملة.",
    "The score must be between 0 and %(max)s.": "يجب أن تكون الدرجة بين 0 و%(max)s.",
    "Saved the grade for %(student)s.": "حُفظت درجة %(student)s.",

    # --- Exams in the question bank -------------------------------------------
    "Exam": "الاختبار",
    "Assignment": "الواجب",
    "Quiz": "الاختبار القصير",
    "Midterm": "اختبار منتصف الفصل",
    "Final": "الاختبار النهائي",
    "Save to": "الحفظ في",
    "Search": "بحث",
    "Search questions": "ابحث في الأسئلة",
    "Show all": "عرض الكل",
    "They are saved to the %(exam)s questions.": "تُحفظ ضمن أسئلة: %(exam)s.",
    "No %(exam)s questions yet. Import them from Word, or add them one by one.":
        "لا توجد أسئلة في %(exam)s بعد. استوردها من ملف Word، أو أضفها واحدًا تلو الآخر.",
    "No %(exam)s question matches \u201c%(search)s\u201d.":
        "لا يوجد سؤال في %(exam)s يطابق \u201c%(search)s\u201d.",
    "This exam has no questions in the bank yet.": "لا توجد أسئلة لهذا الاختبار في البنك بعد.",

    # --- Several files and answer papers --------------------------------------
    "Choose one file or several at once (hold Ctrl). Two kinds of file work:":
        "اختر ملفًا واحدًا أو عدة ملفات معًا (مع الضغط على Ctrl). يُقبل نوعان من الملفات:",
    "A class list: a .csv, .xlsx or Word table with a student ID column and a response "
    "column. English or Arabic column headings both work":
        "كشف الطلاب: ملف .csv أو .xlsx أو جدول في Word فيه عمود للرقم الجامعي وعمود للإجابة. "
        "تصلح عناوين الأعمدة بالعربية أو الإنجليزية",
    "Answer papers: a .docx, .pdf or .txt file per student, holding one answer or the "
    "whole exam with each answer numbered (<code>Q1</code>, <code>1.</code>, "
    "<code>&#1587;1</code>&hellip;). The student ID is read from a line like "
    "<code>Student ID: 441001234</code> at the top, or else from the file name.":
        "أوراق الإجابة: ملف .docx أو .pdf أو .txt لكل طالب، فيه إجابة واحدة أو الاختبار كاملًا "
        "مع ترقيم كل إجابة (<code>Q1</code> أو <code>1.</code> أو <code>&#1587;1</code>&hellip;). "
        "يُقرأ الرقم الجامعي من سطر مثل <code>Student ID: 441001234</code> في أعلى الورقة، "
        "وإلا فمن اسم الملف.",
    "%(first)s and %(count)s more": "%(first)s و%(count)s ملفات أخرى",
    "%(name)s: %(error)s": "%(name)s: %(error)s",
    "'%(name)s' has %(count)s questions but the first file has %(first)s. Every file must "
    "hold the same exam.":
        "في '%(name)s' عدد %(count)s من الأسئلة، بينما في الملف الأول %(first)s. يجب أن تحمل "
        "جميع الملفات الاختبار نفسه.",
    "'%(name)s' is empty.": "الملف '%(name)s' فارغ.",
    "'%(name)s' is larger than 8 MB.": "حجم الملف '%(name)s' أكبر من 8 ميغابايت.",
    "'%(name)s' is not a supported file. Upload .csv or .xlsx tables, or .docx, .pdf or "
    ".txt answer papers.":
        "الملف '%(name)s' غير مدعوم. ارفع جداول .csv أو .xlsx، أو أوراق إجابة .docx أو .pdf "
        "أو .txt.",
    "The answers in '%(name)s' are not numbered, so they cannot be matched to the "
    "%(count)s questions. Start each answer on its own line with its number, like "
    "'Q1', '1.' or 'س1'.":
        "الإجابات في '%(name)s' غير مرقّمة، فلا يمكن مطابقتها مع الأسئلة الـ%(count)s. "
        "ابدأ كل إجابة في سطر مستقل برقمها، مثل 'Q1' أو '1.' أو 'س1'.",
    "No student ID was found in '%(name)s'. Name the file after the student, or start the "
    "paper with a line like 'Student ID: 441001234'.":
        "لم يُعثر على رقم جامعي في '%(name)s'. سمِّ الملف باسم الطالب، أو ابدأ الورقة بسطر "
        "مثل 'Student ID: 441001234'.",
    "No text was found in '%(name)s'. A scanned paper is an image; type the answer into a "
    ".docx or .txt file instead.":
        "لم يُعثر على نص في '%(name)s'. الورقة الممسوحة ضوئيًا صورة؛ اكتب الإجابة في ملف "
        ".docx أو .txt بدلًا منها.",
    "Student ID '%(id)s' appears in both '%(first)s' and '%(second)s'. Each student must "
    "appear once.":
        "الرقم الجامعي '%(id)s' موجود في '%(first)s' وفي '%(second)s'. يجب أن يظهر كل طالب "
        "مرة واحدة.",
    "That is %(count)s files, above the limit of %(limit)s. Upload them in smaller groups.":
        "هذه %(count)s ملفات، وهذا أكثر من الحد البالغ %(limit)s. ارفعها على دفعات أصغر.",
    "These files have %(rows)s students together, above the limit of %(limit)s. Upload "
    "them in smaller groups.":
        "في هذه الملفات %(rows)s طالبًا معًا، وهذا أكثر من الحد البالغ %(limit)s. ارفعها "
        "على دفعات أصغر.",
    "That upload is larger than 32 MB.": "حجم الملفات المرفوعة أكبر من 32 ميغابايت.",
}
