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
    "Close": "إغلاق",
    "Switch to light theme": "التبديل إلى الوضع الفاتح",
    "Switch to dark theme": "التبديل إلى الوضع الداكن",
    "Qayyem &mdash; College of Computing &amp; Informatics, Saudi Electronic University":
        "قيّم &mdash; كلية الحوسبة والمعلوماتية، الجامعة السعودية الإلكترونية",
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
}
