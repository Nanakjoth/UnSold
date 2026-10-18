"""Sample catalogue seed data (spec section 8).

Every entry is sample content (`is_sample_content=True`). Descriptions are
careful and source-conscious: no invented cultural origins, dates, prices, or
safety guarantees. `EDGES` are explicit, reviewable relationship records.
"""

from __future__ import annotations

from typing import Any


def _i(
    *,
    slug: str,
    title: str,
    category: str,
    short: str,
    long: str,
    step: str,
    tags: list[str],
    skills: list[str],
    materials: list[str],
    thinking: list[str],
    access: list[str],
    solo: list[str],
    modes: list[str],
    time: str | None = None,
    difficulty: str | None = None,
    notes: str | None = None,
) -> dict[str, Any]:
    return {
        "slug": slug,
        "title": title,
        "category": category,
        "short_description": short,
        "long_description": long,
        "beginner_step": step,
        "tags": tags,
        "skills": skills,
        "materials": materials,
        "ways_of_thinking": thinking,
        "accessibility_notes": access,
        "solo_or_group": solo,
        "online_or_in_person": modes,
        "time_commitment": time,
        "difficulty": difficulty,
        "languages": ["en"],
        "source_notes": notes
        or "Sample entry written for the prototype catalogue. Verify factual claims before citing.",
        "is_sample_content": True,
    }


ENTRIES: list[dict[str, Any]] = [
    # --- Creative Practices -------------------------------------------------
    _i(
        slug="bookbinding",
        title="Bookbinding",
        category="Creative Practices",
        short="Sewing or gluing pages into hand-made books, from simple pamphlet stitches to case-bound notebooks.",
        long=(
            "Bookbinding turns loose sheets into objects that hold together and open flat. "
            "Beginners usually start with a pamphlet stitch: three holes, one needle, waxed thread. "
            "The craft rewards precise folding and consistent tension more than expensive tools. "
            "Many public libraries run introductory workshops, and the whole first project can be made "
            "with a ruler, a needle, and paper from a printer."
        ),
        step="Make a one-signature pamphlet notebook from three folded sheets and a length of thread.",
        tags=["paper", "craft", "handmade", "notebooks"],
        skills=["folding accuracy", "stitching", "measuring"],
        materials=["paper", "waxed thread or strong thread", "sewing needle", "ruler", "bone folder or butter knife"],
        thinking=["sequencing a process", "tolerance for small imperfections"],
        access=["Seated work; adaptable with adaptive scissors and needle threaders", "Low cost; library workshops often lend tools"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An evening for a first notebook; longer for complex structures",
        difficulty="beginner",
    ),
    _i(
        slug="linocut-printmaking",
        title="Linocut Printmaking",
        category="Creative Practices",
        short="Carving a design into a lino block and hand-pressing prints from it in ink.",
        long=(
            "Linocut is a relief printing technique: you carve away the areas you do not want to "
            "print, roll ink onto the raised surface, and press paper onto it. A single carved block "
            "can produce dozens of identical prints. Beginners often start with a small tile and a "
            "simple shape, because the carving tools remove material in one direction and take "
            "practice to control."
        ),
        step="Carve a small lino tile with a simple shape and pull two or three prints onto scrap paper.",
        tags=["printmaking", "carving", "ink", "editioning"],
        skills=["carving control", "inking evenly", "registration"],
        materials=["lino or soft carving block", "carving tools", "block printing ink", "roller (brayer)", "paper"],
        thinking=["planning in reverse", "iterating on a repeatable process"],
        access=["Carving tools are sharp; cut away from the body and use a bench hook", "Hand-pressing needs no press, so a tabletop works"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A few hours per block; an afternoon to learn the basics",
        difficulty="beginner",
    ),
    _i(
        slug="cyanotype-printing",
        title="Cyanotype Printing",
        category="Creative Practices",
        short="Making deep-blue photographic prints by coating paper with light-sensitive solution and exposing it to sunlight.",
        long=(
            "Cyanotype is an early photographic process that produces blue-and-white images. You coat "
            "paper with an iron-based solution, let it dry in the dark, arrange objects or a negative "
            "on top, and expose it to UV light — usually sunlight. Rinsing in water stops the "
            "reaction and fixes the image. The technique is forgiving, and the characteristic Prussian "
            "blue colour is stable once the print is washed and dried."
        ),
        step="Coat a strip of paper, lay a few leaves on it, expose it in sun for a few minutes, and rinse it in water.",
        tags=["photography", "chemistry", "sunlight", "blue"],
        skills=["coating evenly", "composing with objects", "timing exposures"],
        materials=["cyanotype solution or pre-coated paper", "thick watercolour paper", "glass or frame", "trays of water", "leaves or a negative"],
        thinking=["working with unpredictable light", "embracing one-off variations"],
        access=["Fumes during coating mean doing it in ventilated space with gloves", "Exposure is outdoors, so it is not weather-independent"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Half a day including drying and exposure",
        difficulty="beginner",
    ),
    _i(
        slug="cut-paper-collage",
        title="Cut-Paper Collage",
        category="Creative Practices",
        short="Composing images and shapes from cut or torn paper arranged and glued onto a surface.",
        long=(
            "Collage builds pictures from fragments rather than drawing them from scratch. You can "
            "work with magazine offcuts, painted paper, or plain coloured sheets. The practice suits "
            "people who enjoy arranging and re-arranging, because nothing is fixed until it is glued. "
            "It is one of the cheapest visual arts to start: scissors, paper, and a glue stick are "
            "enough for a first composition."
        ),
        step="Cut five shapes from scrap paper and arrange them into a small composition before gluing.",
        tags=["paper", "composition", "scrap", "abstract"],
        skills=["composition", "cutting", "colour pairing"],
        materials=["assorted paper", "scissors", "glue stick", "backing sheet"],
        thinking=["arrangement before commitment", "seeing relationships between shapes"],
        access=["Seated work; scissors can be swapped for tearable paper", "Very low cost with recycled materials"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a first piece",
        difficulty="beginner",
    ),
    _i(
        slug="stop-motion-animation",
        title="Stop-Motion Animation",
        category="Creative Practices",
        short="Making films by moving objects in tiny increments and photographing each frame.",
        long=(
            "Stop-motion animates still objects by photographing them, moving them slightly, and "
            "photographing again. When the frames play back in sequence, the object appears to move. "
            "Clay, paper cut-outs, and Lego bricks are common materials. A phone camera and a free "
            "app are enough to begin, and the discipline of small, consistent movements is where most "
            "of the learning happens."
        ),
        step="Shoot twelve frames of a small object nudged across a table, then play them back as a short clip.",
        tags=["animation", "film", "clay", "frames"],
        skills=["incremental movement", "consistent framing", "patience"],
        materials=["phone or camera", "small objects or clay", "fixed camera stand or stack of books", "free stop-motion app"],
        thinking=["time as a material", "breaking motion into discrete steps"],
        access=["Shooting can be done seated at a table", "Apps vary in accessibility; most allow large touch targets"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a few seconds of film; longer for stories",
        difficulty="beginner",
    ),
    _i(
        slug="natural-dyeing",
        title="Natural Dyeing",
        category="Creative Practices",
        short="Colouring fibre or cloth with pigments extracted from plants, bark, and other natural sources.",
        long=(
            "Natural dyeing extracts colour from plant material — onion skins, avocado pits, bark, "
            "and leaves are common starting points. Fibre is usually mordanted first so the colour "
            "bonds, then simmered with the dye material. Results vary with the plant, the water, and "
            "the fibre, which is part of the appeal and the frustration. Small swatch tests save "
            "larger pieces from disappointment."
        ),
        step="Dye a small cotton square with onion skins and compare the result before and after rinsing.",
        tags=["textiles", "plants", "colour", "chemistry"],
        skills=["temperature control", "record-keeping", "swatch testing"],
        materials=["plant dye material", "alum or other mordant", "fibrous cloth or yarn", "stainless pot", "gloves"],
        thinking=["controlled experimentation", "accepting variability"],
        access=["Use a dedicated dye pot, not cookware, and work with ventilation", "Mordants are chemicals; follow handling guidance"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A weekend for a first batch including mordanting",
        difficulty="beginner",
    ),
    _i(
        slug="pop-up-paper-engineering",
        title="Pop-Up Paper Engineering",
        category="Creative Practices",
        short="Designing folded mechanisms that make paper structures rise when a page opens.",
        long=(
            "Pop-up books rely on engineered folds: parallel folds, V-folds, and pull-tabs that "
            "translate the opening of a page into movement. The craft sits between origami and "
            "mechanical design, because each mechanism must fold flat without catching. Beginners "
            "learn by copying a single mechanism many times, then combining them."
        ),
        step="Build one parallel-fold pop-up inside a folded card so a shape stands up when opened.",
        tags=["paper", "engineering", "folds", "mechanisms"],
        skills=["geometric folding", "mechanism planning", "precise cutting"],
        materials=["card stock", "craft knife", "cutting mat", "ruler", "glue"],
        thinking=["three-dimensional visualisation", "constraints as design drivers"],
        access=["Craft knives are sharp; a bench hook and mat reduce risk", "Folding can be done seated with a ruler for leverage"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An evening per mechanism; longer for a full card",
        difficulty="beginner",
    ),
    _i(
        slug="origami",
        title="Origami",
        category="Creative Practices",
        short="Folding flat sheets into figures using creases and tucks, without cutting or glue.",
        long=(
            "Origami is the practice of folding a single square sheet into a finished form. Early "
            "models use a handful of creases; complex ones rely on repeatable bases that experienced "
            "folders recognise on sight. The skill is mostly in alignment and crisp creases, and the "
            "material cost is effectively zero once you have paper. Diagrams and video tutorials make "
            "the first models easy to find."
        ),
        step="Fold a traditional paper crane from a single square, following a diagram or video.",
        tags=["paper", "folding", "geometric", "meditative"],
        skills=["crease precision", "spatial reasoning", "following diagrams"],
        materials=["square sheets of paper"],
        thinking=["procedural precision", "patience with intermediate steps"],
        access=["Fully doable seated; adaptive folders exist for limited hand strength", "Paper cost is minimal"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes per simple model; hours for complex ones",
        difficulty="beginner",
    ),
    _i(
        slug="urban-sketching",
        title="Urban Sketching",
        category="Creative Practices",
        short="Drawing the places you are in — streets, cafés, stations — on location, quickly.",
        long=(
            "Urban sketching means drawing from life in the places you find yourself. Sketchbooks are "
            "usually small, tools minimal, and sessions short, because the scene changes. The practice "
            "trains observation more than draughtsmanship: you learn to decide what matters in a view "
            "and to stop before overworking it. Groups often meet to sketch together, but it is "
            "equally a solo habit."
        ),
        step="Spend twenty minutes drawing one street corner or café interior in a small sketchbook.",
        tags=["drawing", "observation", "street", "sketchbook"],
        skills=["quick decision-making", "proportion", "inking without pencil"],
        materials=["small sketchbook", "pen or pencil", "optional small watercolour set"],
        thinking=["seeing before judging", "completeness over polish"],
        access=["Can be done seated indoors or outdoors", "Groups often choose step-free locations"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Twenty minutes to an hour per sketch",
        difficulty="beginner",
    ),
    # --- Making & Repair ----------------------------------------------------
    _i(
        slug="visible-mending",
        title="Visible Mending",
        category="Making & Repair",
        short="Repairing clothing with stitches that are meant to be seen rather than hidden.",
        long=(
            "Visible mending fixes worn clothing by reinforcing the damaged area with deliberate, "
            "decorative stitches instead of invisible ones. A patch behind a hole plus running stitch "
            "or sashiko-style rows can extend a garment's life for years. The approach suits people "
            "who like practical work with a creative surface, and it uses very little thread."
        ),
        step="Patch a small hole in an old garment with a scrap of fabric and rows of running stitch.",
        tags=["textiles", "repair", "sewing", "sustainability"],
        skills=["running stitch", "patch placement", "tension control"],
        materials=["damaged garment", "scrap fabric", "needle", "thread", "scissors"],
        thinking=["repair as visible history", "function before perfection"],
        access=["Seated hand-sewing; thimbles and needle threaders help", "Low cost; practice garments are free"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An evening per small repair",
        difficulty="beginner",
    ),
    _i(
        slug="sashiko-stitching",
        title="Sashiko Stitching",
        category="Making & Repair",
        short="Patterned running-stitch embroidery from Japan, used to reinforce and quilt cloth.",
        long=(
            "Sashiko uses white cotton thread and long running stitches to build geometric patterns "
            "across indigo cloth. Historically it strengthened workwear and quilted layers together; "
            "today it is widely practised as both decoration and repair. Beginners learn an even "
            "stitch length by working rows of straight lines before attempting a pattern. The rhythm "
            "of the stitching is part of why many people find it calming."
        ),
        step="Work three even rows of running stitch on a scrap of fabric using a sashiko or long darner needle.",
        tags=["textiles", "pattern", "stitching", "indigo"],
        skills=["even stitch spacing", "pattern drafting", "rhythm"],
        materials=["cotton fabric", "sashiko thread", "sashiko or darner needle", "ruler", "fabric marker"],
        thinking=["repetition as design", "strength through structure"],
        access=["Seated hand-work; adaptable with needle threaders", "Low material cost"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a practice panel; evenings for a project",
        difficulty="beginner",
        notes="Practice described from publicly available sources; learn with practitioners and community resources rather than from this summary alone.",
    ),
    _i(
        slug="basketry",
        title="Basketry",
        category="Making & Repair",
        short="Weaving containers from plant fibres, cane, or recycled strips.",
        long=(
            "Basketry is among the oldest making traditions, and it exists in very different forms "
            "across cultures. A beginner project usually uses bought cane or paper wicker, which is "
            "soaked to make it pliable, then woven around a simple base. The main skills are keeping "
            "tension even and understanding how rows lock each other down. A small coaster or dish "
            "is a realistic first object."
        ),
        step="Weave a small square mat from paper wicker or cane strips using a simple over-under pattern.",
        tags=["weaving", "fibre", "containers", "handcraft"],
        skills=["tension control", "over-under patterning", "soaking and prep"],
        materials=["soaked cane or paper wiring", "scissors", "basin of water", "simple mould or template"],
        thinking=["structural thinking", "material behaviour"],
        access=["Requires two hands and some grip strength; adapted tools exist", "Cane can be bought cheaply in small packs"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A few hours for a small mat",
        difficulty="beginner",
        notes="Basketry traditions vary widely by region and community; this entry describes the general technique only.",
    ),
    _i(
        slug="clay-modelling",
        title="Clay Modelling",
        category="Making & Repair",
        short="Shaping forms by hand from clay — pinching, coiling, and smoothing.",
        long=(
            "Hand-built clay modelling needs no wheel: you pinch, coil, or slab-build forms and "
            "smooth them with fingers and simple tools. Air-dry clay removes the need for a kiln, "
            "which makes the first projects easy to try at home. The material teaches you about "
            "moisture and timing, because clay that is too dry cracks and too wet collapses."
        ),
        step="Pinch a small bowl from a ball of air-dry clay and set it aside to dry for a day.",
        tags=["clay", "sculpture", "hand-building", "tactile"],
        skills=["pinching evenly", "joining with slip", "smoothing surfaces"],
        materials=["air-dry clay", "scrap paper", "plastic knife or tool", "small bowl of water"],
        thinking=["material timing", "additive and subtractive shaping"],
        access=["Seated work; adaptable with tools for limited grip", "Air-dry clay avoids kiln access entirely"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a first form; days for drying",
        difficulty="beginner",
    ),
    _i(
        slug="miniature-making",
        title="Miniature Making",
        category="Making & Repair",
        short="Building tiny scenes and models — dollhouses, dioramas, and small props.",
        long=(
            "Miniature making builds small-scale scenes from scratch or from kits. It borrows from "
            "model-making, woodworking, and set design, and it rewards patience with tiny components. "
            "A first project might be a single room box or a piece of furniture, because scale "
            "discipline matters more than detail early on. Many builders work at 1:12 scale, which "
            "has a wide market of reference materials."
        ),
        step="Build one simple piece of furniture at a chosen scale from card or balsa.",
        tags=["models", "scale", "diorama", "detail"],
        skills=["scale estimation", "fine cutting", "patience with small parts"],
        materials=["card or balsa", "craft knife", "cutting mat", "tweezers", "glue"],
        thinking=["consistent scale", "modular planning"],
        access=["Requires fine motor control and good light; magnification helps", "Small parts are a hazard around children and pets"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An evening per small component",
        difficulty="beginner",
    ),
    _i(
        slug="recycled-sculpture",
        title="Recycled-Material Sculpture",
        category="Making & Repair",
        short="Making sculptural objects from discarded packaging, e-waste, and other found materials.",
        long=(
            "Recycled sculpture builds art objects from materials that would otherwise be thrown away: "
            "cardboard, bottle caps, broken electronics, and fabric scraps. The constraint of working "
            "with what you have is the point, because it forces creative solutions to joining and "
            "balance. A first piece might be a small assemblage glued or wire-bound onto a base."
        ),
        step="Assemble a small standing figure or object from three or four pieces of clean scrap.",
        tags=["sculpture", "recycling", "assemblage", "junk"],
        skills=["joining dissimilar materials", "balancing forms", "seeing potential in waste"],
        materials=["clean scrap (card, plastic, metal)", "wire or glue", "simple base", "gloves for sharp edges"],
        thinking=["constraint-driven creativity", "material honesty"],
        access=["Sort and clean materials carefully; watch for sharp edges", "Almost free to start"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An afternoon for a first assemblage",
        difficulty="beginner",
    ),
    _i(
        slug="furniture-repair",
        title="Furniture Repair",
        category="Making & Repair",
        short="Fixing chairs, tables, and cabinets — tightening joints, replacing parts, refinishing.",
        long=(
            "Furniture repair keeps usable objects in service: re-gluing loose joints, tightening "
            "screws, replacing a seat web, or refinishing a worn top. Much of it is diagnosis before "
            "tools, because a wobble can come from a leg, a joint, or a floor. Beginners learn the "
            "most from a single simple chair, which is forgiving and useful."
        ),
        step="Diagnose and tighten one loose chair joint, cleaning old glue before re-clamping.",
        tags=["woodwork", "repair", "household", "joinery"],
        skills=["diagnosis", "glue-ups", "clamping"],
        materials=["wood glue", "clamps", "screwdriver", "sandpaper", "damp cloth"],
        thinking=["root-cause diagnosis", "conserving rather than replacing"],
        access=["Some pieces are heavy; get help lifting", "Work can be done seated at a bench or table"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An evening for a simple joint",
        difficulty="beginner",
    ),
    _i(
        slug="bicycle-maintenance",
        title="Bicycle Maintenance",
        category="Making & Repair",
        short="Servicing a bike at home — punctures, brakes, gears, and cleaning.",
        long=(
            "Bicycle maintenance covers the regular work that keeps a bike safe and pleasant: fixing "
            "punctures, adjusting brakes and gears, and cleaning the drivetrain. A few tools handle "
            "most of it, and the feedback is immediate because you can test the result by riding. "
            "Learning to change a tube is the classic first skill, because it removes dependence on "
            "others when you get a flat."
        ),
        step="Remove a wheel, replace an inner tube, and re-inflate it using a patch kit or spare tube.",
        tags=["cycling", "repair", "tools", "mechanical"],
        skills=["tube replacement", "brake adjustment", "cleaning drivetrain"],
        materials=["pump", "tyre levers", "spare tube or patch kit", "degreaser", "rag"],
        thinking=["systematic mechanical diagnosis", "preventive habits"],
        access=["Requires some hand strength for tyres; tools have long levers to help", "Bike can be worked on in a hallway or balcony"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Half an hour for a first puncture; longer for full servicing",
        difficulty="beginner",
    ),
    _i(
        slug="wood-spoon-carving",
        title="Wood Spoon Carving",
        category="Making & Repair",
        short="Carving functional spoons from green wood with a knife and gouge.",
        long=(
            "Spoon carving shapes a usable spoon from green (unseasoned) wood using a sloyd knife and "
            "a hook knife for the bowl. Green wood is softer and easier to cut, and most carvers "
            "work with axes and knives that need careful handling. A first spoon takes an afternoon "
            "and teaches grip, cutting direction, and reading grain more than any tutorial can."
        ),
        step="Carve a simple spatula or spreader from a small piece of green or kiln-dried wood.",
        tags=["wood", "carving", "hand-tools", "functional"],
        skills=["safe cutting grips", "reading grain", "axe control"],
        materials=["green wood blank", "sloyd knife", "hook knife (for bowls)", "bench or vice", "cut-resistant glove"],
        thinking=["working with material direction", "safety as a habit"],
        access=["Sharp tools demand focus and a cut-resistant glove on the holding hand", "Can be done seated with a carving cradle"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An afternoon for a first spoon",
        difficulty="intermediate",
    ),
    # --- Nature & Living Systems --------------------------------------------
    _i(
        slug="seed-saving",
        title="Seed Saving",
        category="Nature & Living Systems",
        short="Collecting and storing seeds from plants you grow, to sow again next season.",
        long=(
            "Seed saving harvests seeds from healthy plants and stores them for the next season. It "
            "starts with simple crops — beans, peas, tomatoes — where the process is easy to see. "
            "The main skills are letting seeds mature fully on the plant and drying them thoroughly "
            "so they keep. Over seasons, saved seed adapts to your particular plot."
        ),
        step="Dry a handful of bean or pea seeds from a healthy plant and store them in a labelled envelope.",
        tags=["gardening", "seeds", "self-sufficiency", "cycles"],
        skills=["harvest timing", "drying and storage", "labelling"],
        materials=["mature seed heads", "paper envelopes", "dry storage jar", "labels"],
        thinking=["long-horizon planning", "observing plant cycles"],
        access=["Can be done seated at a table", "No garden needed; a windowsill works for some crops"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes to collect; a season to see results",
        difficulty="beginner",
    ),
    _i(
        slug="balcony-gardening",
        title="Balcony Gardening",
        category="Nature & Living Systems",
        short="Growing herbs, salad, and compact vegetables in containers on a balcony or windowsill.",
        long=(
            "Balcony gardening grows food and flowers in containers where ground space is absent. The "
            "decisions that matter most are light, drainage, and watering frequency, because pots dry "
            "out faster than beds. Herbs and leafy salad are forgiving first crops, and the yield, "
            "while small, is genuinely usable. It is a practical way to learn plant care in a "
            "contained space."
        ),
        step="Plant one herb pot with drainage holes and place it where it gets a few hours of light.",
        tags=["gardening", "containers", "food", "urban"],
        skills=["watering judgement", "light assessment", "potting"],
        materials=["pots with drainage holes", "potting compost", "seeds or seedlings", "watering can"],
        thinking=["resource budgeting", "observing small changes"],
        access=["Pots can be heavy when wet; wheeled trays or light containers help", "Work can be done at waist height on a table"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour to set up; minutes daily to tend",
        difficulty="beginner",
    ),
    _i(
        slug="compost-science",
        title="Compost Science",
        category="Nature & Living Systems",
        short="Turning kitchen and garden waste into soil improver through controlled decomposition.",
        long=(
            "Composting decomposes organic waste with the help of micro-organisms, given the right "
            "balance of green (nitrogen-rich) and brown (carbon-rich) material, air, and moisture. "
            "A home bin turns scraps into usable matter over months. The practice teaches observation "
            "of temperature, smell, and texture — the signals that tell you whether the balance is "
            "right."
        ),
        step="Start a small compost bin with a mix of green scraps and dry brown material, and turn it once.",
        tags=["soil", "decomposition", "cycles", "household"],
        skills=["carbon-nitrogen balancing", "moisture judgement", "turning"],
        materials=["bin or pile space", "kitchen scraps", "dry leaves or card", "fork or tumbler"],
        thinking=["systems thinking", "patience with slow processes"],
        access=["A tumbler bin avoids bending; worm farms can be indoors", "Manage smells by balancing greens and browns"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes weekly; months to finished compost",
        difficulty="beginner",
    ),
    _i(
        slug="mushroom-observation",
        title="Mushroom Observation",
        category="Nature & Living Systems",
        short="Finding, photographing, and identifying fungi in woods and parks — without picking to eat.",
        long=(
            "Mushroom observation is the practice of noticing, photographing, and identifying fungi "
            "where they grow. It deliberately separates identification from foraging, because eating "
            "a misidentified mushroom can be serious. Beginners learn spore prints, habitat, and "
            "season as the reliable clues. Local mycological groups and public recording projects "
            "give structure to the learning."
        ),
        step="Photograph one fungus where it grows, note its substrate and surroundings, and try to identify it with a field guide.",
        tags=["fungi", "foraging", "identification", "woods"],
        skills=["careful observation", "habitat noting", "photo documentation"],
        materials=["camera or phone", "field guide or identification app", "notebook", "ruler for scale"],
        thinking=["evidence before conclusion", "ecosystem awareness"],
        access=["Woodland paths may be uneven; parks offer easier terrain", "Seasonal and weather-dependent"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A walk of an hour or two",
        difficulty="beginner",
    ),
    _i(
        slug="bird-journaling",
        title="Bird Journaling",
        category="Nature & Living Systems",
        short="Watching and recording the birds you see, building a personal log over time.",
        long=(
            "Bird journaling combines watching birds with keeping a dated record of what you see and "
            "where. Unlike listing for a competition, the emphasis is on attention: behaviour, "
            "sound, weather, and place. A notebook and a pair of binoculars are the main tools, and "
            "a garden or a single park is enough territory to start."
        ),
        step="Spend fifteen minutes watching one spot and write down every bird you see or hear, with the time.",
        tags=["birds", "observation", "journaling", "nature"],
        skills=["field observation", "note-taking", "identification"],
        materials=["notebook", "binoculars (optional)", "field guide or app"],
        thinking=["attention to detail", "building long records"],
        access=["Can be done seated from a window", "Dawn is richest but not required"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Fifteen minutes to a few hours",
        difficulty="beginner",
    ),
    _i(
        slug="tree-identification",
        title="Tree Identification",
        category="Nature & Living Systems",
        short="Learning to name trees by leaf, bark, shape, and season — a gateway skill for naturalists.",
        long=(
            "Tree identification recognises species from leaves, bark, buds, and overall shape. It is "
            "a foundational naturalist skill, because once you can name the trees around you, habitat "
            "and season make more sense. Beginners usually learn a handful of common local species "
            "first, then add more. Winter identification, using buds and bark, is a satisfying later "
            "step."
        ),
        step="Identify three trees on your street using leaf shape and a key, and write down what distinguished them.",
        tags=["trees", "identification", "seasons", "walking"],
        skills=["using a dichotomous key", "comparing leaf shapes", "noticing bark and buds"],
        materials=["field guide or app", "notebook", "optional hand lens"],
        thinking=["classification by evidence", "sharpened observation"],
        access=["Mostly a walking practice, but can be done from a park bench", "Accessible year-round"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A walk; a season to build a local vocabulary",
        difficulty="beginner",
    ),
    _i(
        slug="pollinator-gardening",
        title="Pollinator Gardening",
        category="Nature & Living Systems",
        short="Choosing and arranging plants so bees, butterflies, and other pollinators can feed and nest.",
        long=(
            "Pollinator gardening selects plants and habitats that support bees, butterflies, and "
            "other pollinating insects. It works at any scale — a window box of flowering herbs "
            "counts. The key ideas are season-long flowering, native or well-adapted plants, and "
            "leaving some bare ground and stems for nesting. It rewards recording what visits."
        ),
        step="Plant two or three flowering herbs that bloom at different times and watch what visits them.",
        tags=["gardening", "insects", "ecology", "flowers"],
        skills=["plant selection", "seasonal planning", "observation"],
        materials=["flowering plants", "pots or bed", "water source", "notebook"],
        thinking=["ecosystem design", "long-term planning"],
        access=["Can be done entirely in containers on a balcony", "Some tasks suit seated work"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour to plant; a season to observe",
        difficulty="beginner",
    ),
    _i(
        slug="freshwater-pond-study",
        title="Freshwater Pond Study",
        category="Nature & Living Systems",
        short="Sampling and recording the small life in ponds, ditches, and slow streams.",
        long=(
            "Freshwater study examines the invertebrates and plants in ponds and slow water. A net, "
            "a tray, and an eye for detail are enough to find insect larvae, snails, and water "
            "plants. Because different species indicate different water conditions, the practice "
            "doubles as a window on ecosystem health. Many community science projects accept "
            "records from amateur surveys."
        ),
        step="Scoop a cup of pond water into a white tray and record every visible creature for ten minutes.",
        tags=["water", "invertebrates", "ecology", "sampling"],
        skills=["sampling technique", "identification", "record-keeping"],
        materials=["nets or a jar", "white tray", "hand lens", "notebook or recording app"],
        thinking=["indicator reasoning", "careful sampling"],
        access=["Bank access can be uneven; some ponds have easy platforms", "Not suitable to do alone near deep water"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour or two including travel",
        difficulty="beginner",
    ),
    _i(
        slug="herbarium-plant-pressing",
        title="Herbarium Plant Pressing",
        category="Nature & Living Systems",
        short="Pressing and mounting plant specimens to preserve them for study and reference.",
        long=(
            "Plant pressing preserves specimens flat and dry so they can be studied later. A folded "
            "cardboard press with absorbent paper and a couple of straps is enough; specimens are "
            "changed regularly at first to dry them safely. Mounting and labelling turn a pressed "
            "plant into a reference specimen. The practice connects directly to identification "
            "skills."
        ),
        step="Press one flowering stem between absorbent sheets in a card press, and label it with place and date.",
        tags=["plants", "pressing", "reference", "collection"],
        skills=["specimen selection", "pressing technique", "labelling"],
        materials=["cardboard press or heavy books", "absorbent paper", "specimens", "labels"],
        thinking=["systematic recording", "preservation for study"],
        access=["Mostly seated work; handling delicate specimens suits careful hands", "No garden needed; a walk supplies specimens"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes to set up; weeks of pressing",
        difficulty="beginner",
    ),
    # --- Movement & Play ----------------------------------------------------
    _i(
        slug="indoor-bouldering",
        title="Indoor Bouldering",
        category="Movement & Play",
        short="Climbing short walls over padded floors without ropes, following colour-coded routes.",
        long=(
            "Bouldering routes, called problems, are short and low, so no rope or partner is needed. "
            "Gyms set problems by difficulty and colour, which makes progress measurable. "
            "Fingers and skin tire faster than muscles early on, so beginners improve fastest with short sessions. "
            "Falls are onto padded floors, and gyms supervise the space; learning to fall well is part of the practice."
        ),
        step="Book one introductory gym session and climb every white or easiest-grade problem in one hour.",
        tags=["climbing", "movement", "puzzles", "fitness"],
        skills=["foot placement", "weight shifting", "falling safely"],
        materials=["climbing shoes (rental at gyms)", "chalk (provided or rental)"],
        thinking=["solving movement puzzles", "reading body position"],
        access=["Physical risk of falls; learn proper falling technique with gym staff before climbing alone", "Gyms offer rental gear, so no purchase is needed to try"],
        solo=["solo", "group"],
        modes=["in_person"],
        time="90 minutes per session; weeks to build finger and technique strength",
        difficulty="intermediate",
    ),
    _i(
        slug="orienteering",
        title="Orienteering",
        category="Movement & Play",
        short="Navigating a course between control points using a map and compass, at walk or run pace.",
        long=(
            "Orienteering combines navigation with movement: you follow a course of control points "
            "using only a map and compass, choosing your own route between them. It can be done at "
            "walking pace, which makes it social rather than purely athletic. Beginners learn map "
            "symbols and the discipline of constant re-location — checking where you are against "
            "the map."
        ),
        step="Take a local park map and navigate a short loop of three features, checking your position at each.",
        tags=["navigation", "map", "outdoors", "courses"],
        skills=["map reading", "compass bearings", "route choice"],
        materials=["map", "compass", "watch", "comfortable shoes"],
        thinking=["continuous position-checking", "trade-off decisions"],
        access=["Courses exist for wheelchair and pushchair users on good surfaces", "Can be done at walking pace"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a local course",
        difficulty="beginner",
    ),
    _i(
        slug="juggling",
        title="Juggling",
        category="Movement & Play",
        short="Tossing and catching objects in patterns — starting with three balls.",
        long=(
            "Juggling develops coordination through repeatable throw-catch patterns. Almost everyone "
            "starts with the three-ball cascade, which is learned by building it in stages rather "
            "than attempting the whole pattern at once. Practice is short and frequent, because "
            "improvement comes from repetition rather than duration. The only equipment is three "
            "soft balls."
        ),
        step="Practice the two-ball exchange, throwing and catching in rhythm, until it feels reliable.",
        tags=["coordination", "balls", "patterns", "practice"],
        skills=["rhythm", "hand-eye coordination", "progressive practice"],
        materials=["three soft juggling balls (or socks rolled up)"],
        thinking=["deconstructing a skill", "deliberate repetition"],
        access=["Can be done seated; smaller throws are easier to start", "Balls should be soft and quiet for shared spaces"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Ten minutes daily; weeks for a stable cascade",
        difficulty="beginner",
    ),
    _i(
        slug="improvisational-dance",
        title="Improvisational Dance",
        category="Movement & Play",
        short="Moving expressively without choreography, responding to music, space, and sensation.",
        long=(
            "Improvisational dance moves without fixed choreography, following sensation, music, or "
            "a simple score. It is practiced in studios and community groups, and it requires no "
            "dance training — the entry point is attention to how movement feels rather than how it "
            "looks. Sessions often include warm-up, guided prompts, and open movement."
        ),
        step="Put on a piece of music and move for its full length, following whatever part of your body wants to lead.",
        tags=["dance", "movement", "expression", "somatic"],
        skills=["body awareness", "spatial attention", "improvisation"],
        materials=["open space", "music", "comfortable clothes"],
        thinking=["listening to sensation", "accepting the unplanned"],
        access=["Adaptable to seated movement and small spaces", "Groups often welcome all mobility levels"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A class or a 20-minute home session",
        difficulty="beginner",
    ),
    _i(
        slug="nordic-walking",
        title="Nordic Walking",
        category="Movement & Play",
        short="Walking with two poles in a rhythmic push-off pattern, engaging arms and upper body.",
        long=(
            "Nordic walking uses a pair of poles and a specific push-off technique to turn a walk "
            "into a whole-body exercise. The technique matters more than speed: plant the pole "
            "behind you and push back, coordinating opposite arm and leg. It is low-impact, suits "
            "most fitness levels, and can be done almost anywhere a walk is possible."
        ),
        step="Walk a comfortable route concentrating on planting each pole behind you and pushing back.",
        tags=["walking", "poles", "fitness", "outdoors"],
        skills=["pole timing", "posture", "rhythmic breathing"],
        materials=["pair of walking poles", "comfortable shoes"],
        thinking=["whole-body coordination", "efficiency of movement"],
        access=["Very adaptable; suitable for many mobility levels", "Poles add stability on uneven ground"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="30 minutes to an hour",
        difficulty="beginner",
    ),
    _i(
        slug="slacklining",
        title="Slacklining",
        category="Movement & Play",
        short="Balancing on a flat webbing line tensioned between two anchors.",
        long=(
            "Slacklining balances on a length of flat webbing tensioned between two anchor points, "
            "usually low to the ground. Unlike a tightrope, the line stretches and bounces, so "
            "balance comes from continuous small corrections rather than rigid stillness. Beginners "
            "start with the line at knee height and a spotter, and progress slowly."
        ),
        step="Set a line low between two trees and try to take three steps with a spotter beside you.",
        tags=["balance", "outdoors", "focus", "core"],
        skills=["micro-corrections", "core engagement", "falling safely"],
        materials=["slackline and ratchet or setup kit", "two solid anchors", "flat ground"],
        thinking=["continuous adjustment", "calm under instability"],
        access=["Physical risk of falls; set the line low with soft ground beneath", "Shoulder or joint issues warrant caution and advice"],
        solo=["solo", "group"],
        modes=["in_person"],
        time="30 minutes per session; weeks to walk reliably",
        difficulty="intermediate",
    ),
    _i(
        slug="jump-rope-skills",
        title="Jump-Rope Skills",
        category="Movement & Play",
        short="Skipping with a rope, from basic bounces to crossovers and footwork patterns.",
        long=(
            "Jump-rope builds timing, coordination, and cardiovascular fitness with a single cheap "
            "tool. Most skills build from a basic two-foot bounce, adding speed, crossovers, and "
            "footwork as timing improves. Sessions are short, and the rope length matters more than "
            "the rope quality for a beginner."
        ),
        step="Practise a basic two-foot bounce for thirty seconds at a time until the rhythm holds.",
        tags=["fitness", "coordination", "timing", "cardio"],
        skills=["rhythm", "footwork", "pacing"],
        materials=["adjustable jump rope", "flat shoes or bare feet", "soft surface"],
        thinking=["progressive skill stacking", "pacing effort"],
        access=["Can be adapted with a shorter rope and lower jumps; rope can be swapped for a cord", "Good shock-absorbing surface protects joints"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Ten to twenty minutes",
        difficulty="beginner",
    ),
    _i(
        slug="hula-hooping",
        title="Hula-Hooping",
        category="Movement & Play",
        short="Keeping a hoop rotating around the body with rhythmic hip and core movement.",
        long=(
            "Hula-hooping keeps a weighted hoop in rotation using steady, small movements of the "
            "core and hips. A heavier, larger hoop is genuinely easier to learn with, because it "
            "rotates more slowly. Most people find one side comes quickly; the practice is in "
            "sustaining the rhythm and adding hand and knee tricks."
        ),
        step="Try a larger, heavier hoop and keep it rotating on your waist for a full minute.",
        tags=["fitness", "coordination", "play", "core"],
        skills=["rhythm", "core control", "sustained timing"],
        materials=["appropriately sized hoop", "open space"],
        thinking=["finding a rhythm", "practicing the awkward side"],
        access=["Can be adapted for seated rotation with hands", "Needs a clear space roughly two metres across"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Ten to thirty minutes",
        difficulty="beginner",
    ),
    # --- Music & Sound ------------------------------------------------------
    _i(
        slug="field-recording",
        title="Field Recording",
        category="Music & Sound",
        short="Capturing sounds from the world — streets, rooms, weather, animals — as audio.",
        long=(
            "Field recording captures the sound of places rather than instruments. A phone recorder "
            "is enough to start, though a dedicated recorder gives cleaner results. The practice is "
            "mostly about listening: choosing what to record, waiting for a good moment, and "
            "keeping the mic still. Recordings can become music material or stand alone as documents "
            "of a place."
        ),
        step="Record three minutes of a single location — a market, a park, a room — and listen back with headphones.",
        tags=["audio", "recording", "listening", "places"],
        skills=["mic technique", "listening", "gain staging"],
        materials=["phone or field recorder", "headphones", "windshield (optional)"],
        thinking=["deep listening", "choosing a frame"],
        access=["Doable anywhere sound is; can be done from a seated position", "Headphones should be kept at a safe volume"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes per recording; an hour to collect a set",
        difficulty="beginner",
    ),
    _i(
        slug="diy-instrument-making",
        title="DIY Instrument Making",
        category="Music & Sound",
        short="Building simple playable instruments from household and recycled materials.",
        long=(
            "DIY instrument making builds sound-makers from what is available: rubber-band "
            "guitars, cigar-box style drums, bottle-cap shakers. The point is exploring how "
            "material, tension, and chamber shape change pitch and timbre, not producing a "
            "professional instrument. It is one of the cheapest ways into acoustics."
        ),
        step="Build a rubber-band zither on a tissue box and tune it by stretching the bands.",
        tags=["instruments", "acoustics", "recycling", "sound"],
        skills=["material experimentation", "tuning by ear", "simple construction"],
        materials=["box or container", "rubber bands", "cardboard", "tape", "scissors"],
        thinking=["cause and effect in sound", "iteration through tinkering"],
        access=["Mostly seated work; adaptable for limited grip", "Very low material cost"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a first instrument",
        difficulty="beginner",
    ),
    _i(
        slug="modular-synthesis",
        title="Modular Synthesis",
        category="Music & Sound",
        short="Building sounds by patching together electronic modules that generate and shape signals.",
        long=(
            "Modular synthesis constructs sounds by connecting separate modules — oscillators, "
            "filters, envelopes — with patch cables. Software versions let you learn the whole "
            "system for free on a laptop. The mental shift from presets to modules is significant: "
            "you build a sound from its parts, which teaches signal flow in a way nothing else does."
        ),
        step="In a free software modular environment, patch one oscillator through a filter to an output and shape the filter by hand.",
        tags=["synthesis", "electronic", "signal", "patching"],
        skills=["signal-flow reasoning", "timbre shaping", "systematic experimentation"],
        materials=["computer with free modular software", "headphones or speakers", "MIDI controller (optional)"],
        thinking=["modular systems thinking", "abstracting sound as signal"],
        access=["Screen-based and adaptable; can be done seated", "Free software removes cost barriers"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Hours to learn the basics; ongoing",
        difficulty="intermediate",
    ),
    _i(
        slug="choir-singing",
        title="Choir Singing",
        category="Music & Sound",
        short="Singing in an ensemble, blending your voice into harmony with others.",
        long=(
            "Choir singing places your voice inside an ensemble, listening constantly and adjusting "
            "to blend. No audition is needed for many community choirs, which welcome beginners. "
            "The core skills are breath support, listening sideways, and reading simple notation or "
            "learning by ear. The social dimension is a genuine part of the practice."
        ),
        step="Join a rehearsal or follow a beginner warm-up online, focusing on steady breath and matching pitch.",
        tags=["singing", "ensemble", "harmony", "community"],
        skills=["breath support", "listening and blending", "pitch matching"],
        materials=["voice", "sheet music or learning tracks (optional)", "water"],
        thinking=["listening more than leading", "cooperation through sound"],
        access=["Many choirs are step-free and seated-friendly", "Adapted scores exist for some access needs"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Weekly rehearsals; hours of practice",
        difficulty="beginner",
        notes="Choral traditions vary widely by culture and community; this entry describes community choir participation in general terms.",
    ),
    _i(
        slug="beatboxing",
        title="Beatboxing",
        category="Music & Sound",
        short="Making drum and rhythm sounds with the mouth, lips, tongue, and breath.",
        long=(
            "Beatboxing produces percussion sounds using the vocal apparatus. Beginners start with "
            "three core sounds — kick, hi-hat, snare — and combine them slowly into a pattern. It "
            "is free to practise anywhere and teaches breath control alongside rhythm. Learning "
            "material is abundant online."
        ),
        step="Practise a kick, hi-hat, and snare sound separately, then combine them in a slow three-beat loop.",
        tags=["vocal", "rhythm", "percussion", "voice"],
        skills=["breath control", "sound articulation", "rhythmic layering"],
        materials=["voice", "mirror (optional)"],
        thinking=["isolating physical components", "layering loops"],
        access=["Fully doable seated and silent-friendly with practice", "No equipment needed"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Ten minutes daily; weeks for clean sounds",
        difficulty="beginner",
    ),
    _i(
        slug="sound-design",
        title="Sound Design",
        category="Music & Sound",
        short="Creating and shaping sound effects and textures for film, games, and media.",
        long=(
            "Sound design crafts the non-musical audio in media: footsteps, atmosphere, mechanical "
            "textures, and ambience. It combines field recording with editing and synthesis. "
            "Beginners learn by recreating a scene's sound from scratch, which teaches how much "
            "audio a viewer normally never notices. Free editing software is enough to practise."
        ),
        step="Record three everyday sounds and cut them together to match a short silent video clip.",
        tags=["audio", "film", "editing", "foley"],
        skills=["layering", "editing", "matching picture"],
        materials=["recorder or phone", "free audio editor", "headphones"],
        thinking=["attention to hidden detail", "building texture from parts"],
        access=["Screen and headphone based; doable seated", "Can be practised at home quietly"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An afternoon for a first scene",
        difficulty="beginner",
    ),
    _i(
        slug="songwriting",
        title="Songwriting",
        category="Music & Sound",
        short="Writing words and music together into songs, from simple verses to finished arrangements.",
        long=(
            "Songwriting combines lyric writing with melody and harmony. Most songs grow from a "
            "small seed — a chord loop, a phrase, a rhythm — which is then developed rather than "
            "written from nothing. Beginners benefit from finishing small songs quickly rather than "
            "polishing fragments. A voice recorder on a phone is the essential tool."
        ),
        step="Write four lines over three chords and record a rough voice memo before you forget it.",
        tags=["lyrics", "melody", "chords", "writing"],
        skills=["melodic phrasing", "lyric revision", "structural form"],
        materials=["instrument or voice", "phone recorder", "notebook"],
        thinking=["revision as core practice", "constraint as inspiration"],
        access=["Doable with voice alone or with adaptive instruments", "Writing can be done seated"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes to capture; hours to finish",
        difficulty="beginner",
    ),
    _i(
        slug="relative-pitch-training",
        title="Relative Pitch Training",
        category="Music & Sound",
        short="Training your ear to recognise and reproduce intervals and chord qualities by ear.",
        long=(
            "Relative pitch is the ability to recognise the distance between notes and the quality "
            "of chords without a reference pitch. It can be trained deliberately with intervals, "
            "melodies, and chord progressions. Practice is short and daily, and improvement is "
            "measurable through dictation exercises. It underpins improvisation and transcribing."
        ),
        step="Sing or play two ascending intervals and name them, using a piano or app to check.",
        tags=["ear-training", "intervals", "music-theory", "practice"],
        skills=["interval recognition", "audiation", "pitch matching"],
        materials=["piano or keyboard app", "ear-training app", "notebook"],
        thinking=["deliberate daily practice", "auditory discrimination"],
        access=["Hearing ability varies; vibrotactile and visual aids can substitute", "Short daily sessions suit most schedules"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Ten to twenty minutes daily",
        difficulty="intermediate",
    ),
    _i(
        slug="hand-percussion",
        title="Hand Percussion",
        category="Music & Sound",
        short="Playing drums with the hands — conga, djembe, cajón, and frame drum styles.",
        long=(
            "Hand percussion plays drums directly with the hands, across many instruments and "
            "traditions. Beginners learn tone production — how hand position changes pitch and "
            "attack — before patterns. Instruments like the cajón can be played quietly indoors, "
            "and community sessions welcome newcomers. Technique protects the hands, so posture "
            "matters."
        ),
        step="On any drum or firm surface, alternate open tones and slaps slowly, listening for the difference.",
        tags=["drums", "rhythm", "hands", "ensemble"],
        skills=["tone production", "rhythmic counting", "hand conditioning"],
        materials=["a drum or cajón", "practice pad or firm surface (for silent practice)"],
        thinking=["listening to timbre", "steady time-keeping"],
        access=["Seated playing is standard for many drums", "Start softly to protect hands and joints"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="20 minutes daily; ongoing",
        difficulty="beginner",
        notes="Hand percussion traditions vary by region and community; learn with practitioners rather than from this summary alone.",
    ),
    # --- Food & Culture -----------------------------------------------------
    _i(
        slug="vegetable-fermentation",
        title="Vegetable Fermentation",
        category="Food & Culture",
        short="Salt-brine fermenting of vegetables, such as sauerkraut and kimchi-style mixes, at room temperature.",
        long=(
            "Salted vegetables release their own brine, and lactic acid bacteria preserved this way "
            "have been used across many food traditions for centuries. The core skill is cleanliness "
            "and keeping vegetables under the brine. Batches are usually checked by smell and texture, "
            "and beginners learn with small jars rather than large crocks."
        ),
        step="Shred one cabbage, weigh in 2% salt, pack it under its own brine in a clean jar, and wait one week.",
        tags=["fermentation", "food", "preservation", "kitchen"],
        skills=["salt ratios", "cleanliness discipline", "sensory checking"],
        materials=["cabbage or other vegetables", "non-iodised salt", "clean glass jar", "weight to keep vegetables submerged"],
        thinking=["patience with slow processes", "observation over instruction-following"],
        access=["No special equipment needed; jars are widely available cheaply", "Anyone with dietary restrictions should check fermented foods with a clinician first"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="20 minutes of active work; one to three weeks of waiting",
        difficulty="beginner",
        notes="Fermentation practices belong to many distinct food traditions; this entry describes the general technique only. Learn regional styles from cooks and community resources.",
    ),
    _i(
        slug="sourdough-bread",
        title="Sourdough Bread",
        category="Food & Culture",
        short="Leavening bread with a living starter of flour and water instead of commercial yeast.",
        long=(
            "Sourdough uses a fermented flour-and-water starter to raise bread, giving a slower rise "
            "and a characteristic flavour. The starter is a living culture that must be fed and "
            "observed, which makes baking as much about timing as recipe. Beginners learn hydration, "
            "bulk fermentation, and shaping — the three places most failures happen."
        ),
        step="Feed a starter, then bake one simple loaf following a beginner recipe and note the timings.",
        tags=["bread", "fermentation", "baking", "starter"],
        skills=["starter maintenance", "shaping", "timing judgement"],
        materials=["flour", "water", "salt", "jar", "oven", "bowl"],
        thinking=["reading a living process", "adjusting to conditions"],
        access=["Kneading can be adapted or use no-knead methods", "Oven use requires standard kitchen safety"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Days for a starter; a day per bake",
        difficulty="beginner",
    ),
    _i(
        slug="spice-blending",
        title="Spice Blending",
        category="Food & Culture",
        short="Combining ground spices into blends for particular cuisines and dishes.",
        long=(
            "Spice blending mixes ground spices into balanced blends — garam masala, ras el hanout, "
            "five-spice, and many household mixes. The skill lies in balance: warm, sweet, bitter, "
            "and pungent notes in proportion. Buying whole spices and grinding them fresh makes a "
            "noticeable difference, and blends are best made in small batches."
        ),
        step="Toast and grind three whole spices and mix them in equal parts to taste the result.",
        tags=["spices", "cooking", "flavour", "blending"],
        skills=["toasting and grinding", "flavour balancing", "ratio adjustment"],
        materials=["whole spices", "pan for toasting", "grinder or mortar and pestle"],
        thinking=["adjusting by taste", "building balance"],
        access=["Seated kitchen work; pre-ground spices work if grinding is difficult", "Low cost to start with three spices"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Half an hour for a small batch",
        difficulty="beginner",
        notes="Spice blends belong to specific food traditions; this entry describes the general practice of blending, not any single cultural recipe.",
    ),
    _i(
        slug="home-pickling",
        title="Home Pickling",
        category="Food & Culture",
        short="Preserving vegetables in vinegar or brine, from quick pickles to longer ferments.",
        long=(
            "Pickling preserves vegetables in an acidic medium — vinegar for quick pickles, brine for "
            "fermented ones. Quick pickling is the gentler entry: vegetables, a hot vinegar brine, "
            "and a jar, ready within days. The practice teaches acidity, sugar, and salt balance, "
            "and safe jar handling. It is a good way to use glut produce."
        ),
        step="Make one jar of quick-pickled cucumber or carrot slices and chill them for two days.",
        tags=["preservation", "vegetables", "vinegar", "pantry"],
        skills=["brine ratios", "jar hygiene", "flavour balancing"],
        materials=["vegetables", "vinegar", "water", "sugar and salt", "clean jars"],
        thinking=["balancing sour, sweet, and salt", "planning for later use"],
        access=["Seated kitchen work; jars can be heavy when full", "Follow tested recipes for safety"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Half an hour; days for flavour to develop",
        difficulty="beginner",
    ),
    _i(
        slug="jam-preserving",
        title="Jam and Preserve Making",
        category="Food & Culture",
        short="Cooking fruit with sugar to set it into jam, jelly, or preserve.",
        long=(
            "Jam making cooks fruit with sugar to a set point where pectin gels the result. The "
            "practice is exacting about temperature and timing, and it rewards small batches. "
            "Beginners learn the wrinkle test and the setting point, which are more reliable than "
            "timings alone. Seasonal fruit is the traditional driver."
        ),
        step="Cook a small batch of soft fruit with sugar and test the set with the cold-plate wrinkle test.",
        tags=["fruit", "sugar", "preserving", "seasonal"],
        skills=["setting-point judgement", "hot sugar handling", "batch planning"],
        materials=["fruit", "sugar", "preserving pan", "jam jars", "thermometer or cold plate"],
        thinking=["precision under time pressure", "working with seasons"],
        access=["Handling hot sugar requires care and possibly help", "Seated work is possible with a stable pan"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An afternoon per batch",
        difficulty="beginner",
    ),
    _i(
        slug="coffee-brewing",
        title="Coffee Brewing",
        category="Food & Culture",
        short="Brewing coffee by controlling grind, ratio, water, and time — pour-over, press, or espresso.",
        long=(
            "Coffee brewing is a small exercise in controlled variables: grind size, dose, water "
            "temperature, and brew time. Changing one moves the result noticeably, which makes the "
            "drink a useful teacher. Pour-over and press methods are cheap to start with, and "
            "tasting side by side teaches more than any recipe."
        ),
        step="Brew two cups with the same coffee at different grind sizes and compare the taste.",
        tags=["coffee", "brewing", "taste", "ratio"],
        skills=["grind and ratio control", "tasting comparison", "pour technique"],
        materials=["coffee and grinder", "kettle", "brewer (pour-over or press)", "scale"],
        thinking=["isolating variables", "learning by comparison"],
        access=["Seated kitchen work; automatic machines reduce physical steps", "Caffeine sensitivity should be managed"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Ten minutes per brew",
        difficulty="beginner",
    ),
    _i(
        slug="tea-brewing",
        title="Tea Brewing",
        category="Food & Culture",
        short="Preparing different teas with attention to leaf, water temperature, and steeping time.",
        long=(
            "Tea brewing varies leaf, temperature, and time to bring out different characters. Green "
            "and white teas are damaged by boiling water; black and herbal teas generally want it. "
            "The practice is a study in small variables, and comparing side-by-side brews is the "
            "fastest way to learn. A thermometer or a watched kettle is enough precision to start."
        ),
        step="Brew one tea twice — once at a lower temperature and once with boiling water — and compare.",
        tags=["tea", "brewing", "taste", "ritual"],
        skills=["temperature control", "steeping timing", "sensory comparison"],
        materials=["loose leaf tea", "kettle", "infuser or pot", "timer", "thermometer (optional)"],
        thinking=["attending to small differences", "calm repetition"],
        access=["Seated work with a kettle; adapt with lighter vessels", "Caffeine can be managed by choice of leaf"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes per session",
        difficulty="beginner",
        notes="Tea practices carry deep cultural histories in many regions; this entry describes general brewing variables, not any single ceremonial tradition.",
    ),
    _i(
        slug="dumpling-folding",
        title="Dumpling Folding",
        category="Food & Culture",
        short="Wrapping fillings in dough with a variety of pleats and shapes, then cooking them.",
        long=(
            "Dumpling folding is a widespread technique found in many cuisines, each with its own "
            "shapes and fillings. The folding is learnable in an afternoon, and the pleating "
            "improves with repetition. Beginners often start with a simple half-moon or a basic "
            "pleat, because a good seal matters more than an elaborate shape."
        ),
        step="Fold five dumplings with a simple half-moon pleat and pan-fry or boil them.",
        tags=["dough", "folding", "filling", "shared-meal"],
        skills=["pleating", "sealing", "portioning filling"],
        materials=["wrappers or simple dough", "filling", "bowl of water", "pan or steamer"],
        thinking=["repetition building skill", "feeding others"],
        access=["Seated table work; adaptive tools exist for limited grip", "Low cost; a batch feeds several"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour including cooking",
        difficulty="beginner",
        notes="Dumpling traditions vary across many cultures; this entry describes the general folding technique, and specific styles are best learned from cooks of those traditions.",
    ),
    _i(
        slug="seasonal-cooking",
        title="Seasonal Cooking",
        category="Food & Culture",
        short="Planning and cooking around what is abundant and cheap in the current season.",
        long=(
            "Seasonal cooking builds meals around produce that is currently in season, which is "
            "usually cheaper and better. It asks for planning: knowing what is abundant, storing "
            "surplus, and improvising from a box of vegetables rather than a fixed recipe. The "
            "practice reduces waste and reconnects cooking to weather and place."
        ),
        step="Buy three vegetables that are in season this week and plan two meals from them.",
        tags=["vegetables", "planning", "household", "sustainability"],
        skills=["menu planning", "improvising with odds and ends", "storage knowledge"],
        materials=["seasonal produce", "basic pantry", "notebook or app"],
        thinking=["planning around abundance", "reducing waste"],
        access=["Seated planning and kitchen work; delivery boxes reduce shopping effort", "Budget-friendly with planning"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour of planning plus cooking",
        difficulty="beginner",
    ),
    # --- Design & Visual Thinking -------------------------------------------
    _i(
        slug="typography-basics",
        title="Typography Basics",
        category="Design & Visual Thinking",
        short="Choosing and arranging type so text is legible, hierarchical, and pleasant to read.",
        long=(
            "Typography is the craft of arranging type. Its first duty is legibility, and its second "
            "is hierarchy — signalling what matters through size, weight, and spacing. Beginners "
            "learn most by setting the same paragraph in two typefaces and comparing how each feels "
            "to read. Line length and spacing matter more than choosing between similar faces."
        ),
        step="Set the same short paragraph in two different typefaces and compare which reads more easily.",
        tags=["type", "layout", "legibility", "design"],
        skills=["hierarchy design", "line and spacing judgement", "typeface comparison"],
        materials=["any layout app or paper", "two typefaces", "a short text"],
        thinking=["reading from the reader's side", "subtle distinctions"],
        access=["Screen-based and doable seated", "Magnification makes comparison easier"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a first comparison",
        difficulty="beginner",
    ),
    _i(
        slug="data-storytelling",
        title="Data Storytelling",
        category="Design & Visual Thinking",
        short="Turning numbers into a clear narrative with charts, context, and honest framing.",
        long=(
            "Data storytelling selects and orders evidence so a reader can follow a point. It "
            "combines chart choice, annotation, and narrative sequencing. The ethical dimension is "
            "central: framing, scale, and omission all change what an audience concludes. Beginners "
            "learn by re-charting the same dataset three ways and seeing how the story shifts."
        ),
        step="Take a small public dataset and make three charts of it that emphasise different points.",
        tags=["charts", "narrative", "evidence", "honesty"],
        skills=["chart selection", "framing", "annotation"],
        materials=["spreadsheet or plotting tool", "public dataset", "writing"],
        thinking=["framing effects", "evidence before conclusion"],
        access=["Screen-based; charts can be made with keyboard-only tools", "Colour-blind-safe palettes matter"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A few hours per story",
        difficulty="beginner",
    ),
    _i(
        slug="information-design",
        title="Information Design",
        category="Design & Visual Thinking",
        short="Structuring information — diagrams, forms, instructions — so people can use it quickly.",
        long=(
            "Information design makes complex material usable: instructions, diagrams, forms, and "
            "timetables. It draws on writing, layout, and testing with real readers. The discipline "
            "is defined by outcomes — did the reader succeed? — rather than aesthetics. Beginners "
            "learn by redesigning a confusing form or set of instructions and testing it on someone."
        ),
        step="Redesign a page of confusing instructions so a friend can follow them without help.",
        tags=["diagrams", "clarity", "instructions", "usability"],
        skills=["sequencing", "labelling", "user testing"],
        materials=["pen and paper", "the original document", "a tester"],
        thinking=["designing for the reader's task", "testing over assuming"],
        access=["Seated work; adaptable tools widely available", "Testing can be done remotely"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A few hours for a first redesign",
        difficulty="beginner",
    ),
    _i(
        slug="accessible-design-thinking",
        title="Accessible Design Thinking",
        category="Design & Visual Thinking",
        short="Designing so people with different abilities can use what you make, from the start.",
        long=(
            "Accessible design considers the full range of human ability from the outset rather than "
            "adding accommodations later. It covers contrast, keyboard use, captions, plain "
            "language, and physical reach. The practice is grounded in consulting disabled users "
            "rather than guessing. Beginners learn most by auditing a familiar product against "
            "simple guidelines."
        ),
        step="Audit a website or document for contrast, keyboard access, and alt text, and fix three issues.",
        tags=["accessibility", "inclusion", "design", "testing"],
        skills=["guideline application", "contrast checking", "consulting users"],
        materials=["a product to audit", "contrast checker", "guideline reference"],
        thinking=["assumption testing", "designing for range"],
        access=["The practice itself is highly accessible and remote-friendly", "Real disabled-user input is central"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A few hours for a first audit",
        difficulty="beginner",
    ),
    _i(
        slug="sketchnoting",
        title="Sketchnoting",
        category="Design & Visual Thinking",
        short="Taking visual notes that mix simple drawings, text, and layout to capture ideas.",
        long=(
            "Sketchnoting combines words and simple drawings to record talks, books, or plans. The "
            "drawings are deliberately basic — arrows, boxes, stick figures — because the goal is "
            "capture, not illustration. The practice improves retention and is fast enough for live "
            "note-taking. A pen and any notebook are the whole kit."
        ),
        step="Sketchnote a short talk or video using only boxes, arrows, and a few words per idea.",
        tags=["notes", "drawing", "visual", "learning"],
        skills=["visual hierarchy", "simplified drawing", "live capture"],
        materials=["notebook", "pen or marker"],
        thinking=["dual coding", "distilling to essentials"],
        access=["Seated work; digital tablets offer adaptive input", "Words alone are a valid starting point"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="The length of the talk; minutes of practice",
        difficulty="beginner",
    ),
    _i(
        slug="icon-design",
        title="Icon Design",
        category="Design & Visual Thinking",
        short="Designing small symbols that communicate an action or object at a glance.",
        long=(
            "Icon design compresses meaning into a small, repeatable symbol. It requires decisions "
            "about grid, stroke weight, and metaphor that hold up when the icon is tiny. Beginners "
            "learn by redrawing a set of everyday icons on one grid and noticing where meaning "
            "breaks down. Consistency across a set matters more than any single icon."
        ),
        step="Draw five app icons on the same grid with the same stroke weight and test them small.",
        tags=["symbols", "grid", "ui", "clarity"],
        skills=["metaphor choice", "grid discipline", "legibility at size"],
        materials=["pen and grid paper", "or a vector drawing tool"],
        thinking=["constraint-driven abstraction", "consistency as a system"],
        access=["Digital tools support zoom and keyboard drawing", "Seated work"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a small set",
        difficulty="beginner",
    ),
    _i(
        slug="layout-and-grids",
        title="Layout and Grids",
        category="Design & Visual Thinking",
        short="Organising pages with underlying grids so content aligns and reads consistently.",
        long=(
            "Layout grids give a page a hidden structure that content aligns to, producing "
            "consistency across pages. Beginners learn columns, margins, and baseline rhythm by "
            "setting the same content on two different grids and comparing. The skill transfers to "
            "documents, slides, and web pages alike."
        ),
        step="Lay out the same text and image on a 6-column and a 12-column grid and compare the feel.",
        tags=["grid", "alignment", "layout", "consistency"],
        skills=["column planning", "alignment discipline", "spacing rhythm"],
        materials=["any layout tool", "grid overlay", "sample content"],
        thinking=["structure enabling freedom", "systematic consistency"],
        access=["Screen-based and adaptable", "Doable seated with keyboard navigation"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A few hours for a first exercise",
        difficulty="beginner",
    ),
    _i(
        slug="poster-composition",
        title="Poster Composition",
        category="Design & Visual Thinking",
        short="Designing a single-sheet poster that works at a glance and rewards a second look.",
        long=(
            "Poster composition balances one dominant message with supporting detail on a single "
            "sheet. It forces decisions about hierarchy, type scale, and image placement that "
            "smaller formats let you avoid. Beginners learn by designing at actual size, because "
            "scale changes everything. The classic test is viewing from across a room."
        ),
        step="Design a poster for a fictional event that is legible from three metres away.",
        tags=["poster", "hierarchy", "print", "composition"],
        skills=["hierarchy at scale", "type sizing", "image placement"],
        materials=["layout tool or paper and pens", "one image", "the event details"],
        thinking=["communicating at a distance", "editing to one message"],
        access=["Seated work; digital tools are fully adaptable", "Can be made at home with a printer"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An afternoon for a first poster",
        difficulty="beginner",
    ),
    _i(
        slug="colour-theory",
        title="Colour Theory",
        category="Design & Visual Thinking",
        short="Understanding how colours relate, interact, and carry meaning in composition.",
        long=(
            "Colour theory describes relationships between colours — hue, saturation, value — and "
            "how they behave together. It is partly formal (complementary and analogous schemes) and "
            "partly cultural and contextual. Beginners learn most by mixing a limited palette and "
            "noticing what value, not hue, does to readability."
        ),
        step="Make a small palette of three colours plus white and black, and test it for contrast.",
        tags=["colour", "palette", "contrast", "perception"],
        skills=["palette building", "contrast judgement", "value awareness"],
        materials=["paints, markers, or a digital tool", "a swatch sheet"],
        thinking=["value over hue", "context-dependent meaning"],
        access=["Digital tools support colour-blind simulation", "Doable seated"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a first palette",
        difficulty="beginner",
    ),
    # --- Games & Strategy ---------------------------------------------------
    _i(
        slug="chess-variants",
        title="Chess Variants",
        category="Games & Strategy",
        short="Playing chess with altered rules — different boards, pieces, or win conditions.",
        long=(
            "Chess variants change the rules of chess: different starting positions, new pieces, "
            "asymmetric sides, or altered objectives. They are useful because they level the field "
            "between stronger and weaker players and reward fresh thinking. Many variants are free "
            "to play online and take minutes to learn."
        ),
        step="Learn one variant — such as a shortened or asymmetrical version — and play three games.",
        tags=["strategy", "boards", "variants", "rules"],
        skills=["pattern thinking", "adaptation", "planning ahead"],
        materials=["chess set or free online platform", "the variant's rules"],
        thinking=["questioning inherited assumptions", "transferring skills to new rules"],
        access=["Many variants are playable online and seated", "Board size can be adjusted"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="20 minutes to hours per game",
        difficulty="beginner",
    ),
    _i(
        slug="go",
        title="Go",
        category="Games & Strategy",
        short="An ancient territory game of placing stones on a large board — simple rules, deep play.",
        long=(
            "Go is played by placing stones on the intersections of a large board, surrounding "
            "territory rather than capturing pieces directly. The rules fit on a page, but the "
            "strategy is famously deep. Beginners learn the balance between expanding and securing, "
            "and the concept of living and dead groups. Handicaps make games between different "
            "levels competitive."
        ),
        step="Learn the rules of Go and play a nine-by-nine board game against a friend or app.",
        tags=["strategy", "territory", "boards", "patience"],
        skills=["spatial reasoning", "trade-off judgement", "pattern recognition"],
        materials=["a Go board (or a paper grid)", "stones (or two colours of beads)", "free online client"],
        thinking=["long-term positioning", "knowing when to stop"],
        access=["Playable online and seated; boards come in many sizes", "Handicaps help mixed-ability games"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="20 minutes to hours per game",
        difficulty="beginner",
    ),
    _i(
        slug="mechanical-puzzle-solving",
        title="Mechanical Puzzle Solving",
        category="Games & Strategy",
        short="Solving interlocking, disentanglement, and assembly puzzles with your hands.",
        long=(
            "Mechanical puzzles are physical objects to be taken apart, reassembled, or untangled. "
            "They reward patience and observation more than calculation, because the solution is "
            "often a small non-obvious move. Beginners learn to track what they have tried and to "
            "reset properly. Puzzles are cheap, portable, and endlessly varied."
        ),
        step="Take a simple interlocking puzzle apart and reassemble it, timing yourself on the second run.",
        tags=["puzzles", "tactile", "logic", "patience"],
        skills=["systematic exploration", "spatial reasoning", "persistence"],
        materials=["a physical puzzle", "patience"],
        thinking=["hypothesis testing by hand", "learning from dead ends"],
        access=["Seated and tactile; larger-piece puzzles exist", "Some puzzles need significant hand strength"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes to hours per puzzle",
        difficulty="beginner",
    ),
    _i(
        slug="puzzle-design",
        title="Puzzle Design",
        category="Games & Strategy",
        short="Creating puzzles — for games, escape rooms, or paper — with fair clues and solutions.",
        long=(
            "Puzzle design builds challenges that are solvable through insight rather than guessing. "
            "The craft lies in clue placement: giving enough that the solution feels earned, and no "
            "more. Beginners learn by building a small puzzle, watching someone attempt it, and "
            "seeing exactly where they get stuck. Playtesting is the core method."
        ),
        step="Design a three-clue puzzle for a friend and watch them solve it without helping.",
        tags=["puzzles", "clues", "design", "playtesting"],
        skills=["clue sequencing", "fairness judgement", "observing play"],
        materials=["paper and pens", "a willing tester", "optional envelopes and locks"],
        thinking=["designing for the solver", "iterating from observation"],
        access=["Can be made entirely on paper or digitally", "Seated and remote-friendly"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="A few hours including testing",
        difficulty="beginner",
    ),
    _i(
        slug="cooperative-board-games",
        title="Cooperative Board Games",
        category="Games & Strategy",
        short="Playing board games where all players work together against the game itself.",
        long=(
            "Cooperative games set players against a shared challenge rather than each other. The "
            "social dynamic changes completely: discussion, planning, and shared wins replace "
            "elimination. Beginners learn shared decision-making, including the common trap of one "
            "player quarterbacking. Many cooperative games are quick to teach."
        ),
        step="Play one cooperative game with friends, agreeing aloud before each turn what the group should do.",
        tags=["cooperation", "boards", "planning", "social"],
        skills=["shared decision-making", "collective planning", "communication"],
        materials=["a cooperative board game", "two or more players"],
        thinking=["winning as a group", "negotiating disagreement"],
        access=["Many games are seated and table-friendly", "Rule summaries help new players"],
        solo=["group"],
        modes=["online", "in_person"],
        time="30 minutes to two hours",
        difficulty="beginner",
    ),
    _i(
        slug="card-game-design",
        title="Card Game Design",
        category="Games & Strategy",
        short="Designing card games — balancing luck, skill, and the flow of a short match.",
        long=(
            "Card game design builds play from a deck: rules for playing cards, conditions for "
            "winning, and the balance between luck and skill. Prototyping is fast with blank cards "
            "or paper. The crucial step is watching people play and noticing where the game stalls "
            "or feels unfair. Iteration is where design actually happens."
        ),
        step="Prototype a ten-card game, play it three times, and change one rule between each game.",
        tags=["cards", "game-design", "balance", "prototyping"],
        skills=["rule writing", "balance tuning", "rapid prototyping"],
        materials=["blank cards or paper", "pens", "testers"],
        thinking=["emergent behaviour", "iteration from observation"],
        access=["Paper prototypes are cheap and adaptable", "Seated play"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An evening per prototype round",
        difficulty="beginner",
    ),
    _i(
        slug="improv-games",
        title="Improv Games",
        category="Games & Strategy",
        short="Playing theatre improv exercises that build spontaneity, listening, and ensemble trust.",
        long=(
            "Improv games are short exercises built on accepting offers and building on them. They "
            "are played in comedy and drama groups, but the skills — listening, quick thinking, "
            "supporting others — transfer widely. Beginners start with simple accept-and-build "
            "games where the point is participation rather than performance."
        ),
        step="Play a simple accept-and-build circle game where each person adds one sentence to a story.",
        tags=["theatre", "spontaneity", "listening", "ensemble"],
        skills=["active listening", "accepting offers", "ensemble support"],
        materials=["two or more players", "optional prompts or dice"],
        thinking=["saying yes to offers", "supporting over competing"],
        access=["Can be played seated and online", "Low pressure; games are short"],
        solo=["group"],
        modes=["online", "in_person"],
        time="20 minutes to an hour",
        difficulty="beginner",
    ),
    _i(
        slug="escape-room-design",
        title="Escape Room Design",
        category="Games & Strategy",
        short="Building home escape-room experiences with puzzles, props, and a narrative thread.",
        long=(
            "Escape room design assembles puzzles into a themed experience with a timer and a "
            "story. The discipline is in flow: puzzles should connect, hint gradually, and avoid "
            "one broken step stopping everything. Home versions use printed puzzles, locks, and "
            "household props. Playtesting reveals where players stall."
        ),
        step="Design a five-puzzle home escape room for friends with a 30-minute timer and hints on request.",
        tags=["escape-room", "puzzles", "narrative", "events"],
        skills=["puzzle chaining", "pacing", "hint design"],
        materials=["printed puzzles", "lockbox or combination locks", "props", "timer"],
        thinking=["designing a flow", "graceful difficulty curves"],
        access=["Puzzles can be adapted for seated players and various senses", "Physical locks can be swapped for paper ones"],
        solo=["group"],
        modes=["online", "in_person"],
        time="An evening to build; an hour to play",
        difficulty="beginner",
    ),
    # --- Science & Everyday Experiments --------------------------------------
    _i(
        slug="backyard-astronomy",
        title="Backyard Astronomy",
        category="Science & Everyday Experiments",
        short="Observing the night sky — moon phases, planets, and constellations — with eyes or binoculars.",
        long=(
            "Backyard astronomy observes the sky from home. The moon, planets, and bright stars are "
            "reachable without a telescope, and binoculars reveal craters and moons of Jupiter. "
            "Beginners learn the seasonal sky and the discipline of letting eyes dark-adapt. Free "
            "planetarium apps make identification approachable."
        ),
        step="Go outside after dark, let your eyes adjust for ten minutes, and identify three constellations with an app.",
        tags=["astronomy", "night", "observation", "sky"],
        skills=["sky navigation", "dark adaptation", "patience"],
        materials=["your eyes", "binoculars (optional)", "red-light torch", "star chart or app"],
        thinking=["long-distance observation", "seasonal cycles"],
        access=["Can be done seated outdoors or from a window", "Cold and late hours are the main barrier"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="30 minutes to hours on clear nights",
        difficulty="beginner",
    ),
    _i(
        slug="amateur-microscopy",
        title="Amateur Microscopy",
        category="Science & Everyday Experiments",
        short="Exploring the microscopic world — pond water, cells, and crystals — with a microscope.",
        long=(
            "Amateur microscopy reveals the structure of everyday materials at high magnification. "
            "A basic compound microscope and prepared or homemade slides open up pond life, plant "
            "cells, and fibres. Beginners learn focusing technique and slide preparation, which "
            "matters more than the microscope's specifications. Many clubs lend equipment."
        ),
        step="Put a drop of pond water on a slide and focus on the smallest moving things you can find.",
        tags=["microscope", "cells", "science", "exploration"],
        skills=["slide preparation", "focusing technique", "recording observations"],
        materials=["compound microscope", "slides and cover slips", "dropper", "specimens"],
        thinking=["scale-shifting curiosity", "careful observation"],
        access=["Seated bench work; adapted stages exist for limited dexterity", "Equipment can be borrowed from clubs"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour per session",
        difficulty="beginner",
    ),
    _i(
        slug="weather-journaling",
        title="Weather Journaling",
        category="Science & Everyday Experiments",
        short="Recording daily weather — temperature, cloud, wind, and pressure — to see patterns.",
        long=(
            "Weather journaling keeps a daily record of conditions, building a personal dataset "
            "over months. The value is in noticing patterns: how pressure moves ahead of rain, how "
            "your local valley behaves. A notebook is enough, though a basic digital thermometer "
            "and app add precision. The practice connects directly to citizen weather networks."
        ),
        step="Record temperature, cloud type, and wind for seven days, and look for a pattern on day seven.",
        tags=["weather", "recording", "patterns", "citizen-science"],
        skills=["consistent recording", "pattern spotting", "instrument reading"],
        materials=["notebook", "thermometer", "barometer app (optional)"],
        thinking=["data over time", "predictive pattern recognition"],
        access=["Can be done from a window; recording is fully adaptable", "Daily routine is the main commitment"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Five minutes daily",
        difficulty="beginner",
    ),
    _i(
        slug="cloud-spotting",
        title="Cloud Spotting",
        category="Science & Everyday Experiments",
        short="Identifying cloud types and using them to read the weather overhead.",
        long=(
            "Cloud spotting identifies cloud genera — cumulus, stratus, cirrus, and their variants — "
            "and reads them for approaching weather. It is one of the quickest entry points into "
            "observational science, needing only the sky. Beginners learn the basic types and the "
            "stories their changes tell about moisture and instability."
        ),
        step="Identify three different cloud types on one day and note whether the weather changed after.",
        tags=["clouds", "weather", "observation", "sky"],
        skills=["classification", "pattern observation", "weather reading"],
        materials=["cloud identification guide or app", "notebook"],
        thinking=["classification by evidence", "forecasting from signs"],
        access=["Doable entirely from a window or doorstep", "Free and year-round"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes a day",
        difficulty="beginner",
    ),
    _i(
        slug="simple-electronics",
        title="Simple Electronics",
        category="Science & Everyday Experiments",
        short="Building basic circuits — lighting LEDs, buzzing speakers, sensing touch — on a breadboard.",
        long=(
            "Simple electronics builds working circuits from a battery, a breadboard, and a few "
            "components. Beginners learn to read a schematic, place components, and troubleshoot a "
            "circuit that does not work — usually a swapped lead or a blown LED. A starter kit "
            "covers the first months of projects."
        ),
        step="Build a circuit on a breadboard that lights an LED through a push-button switch.",
        tags=["electronics", "circuits", "breadboard", "hardware"],
        skills=["reading schematics", "troubleshooting", "component identification"],
        materials=["breadboard", "battery pack", "LEDs, resistors, buttons", "jumper wires"],
        thinking=["systematic debugging", "reading formal diagrams"],
        access=["Seated bench work; adaptable tools exist for limited dexterity", "Low-voltage kits are safe with normal care"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An evening per project",
        difficulty="beginner",
    ),
    _i(
        slug="paper-circuits",
        title="Paper Circuits",
        category="Science & Everyday Experiments",
        short="Building simple electrical circuits on paper with copper tape, coin cells, and LEDs.",
        long=(
            "Paper circuits use conductive copper tape as wire and a coin cell battery as power. "
            "A single LED and a taped switch are enough to learn what a closed loop is. "
            "The same technique scales to light-up cards and simple sensors. "
            "Coin cells must be kept away from small children because swallowing them is dangerous."
        ),
        step="Tape one LED and one coin cell to a card so the circuit closes when the card folds shut.",
        tags=["electronics", "paper", "circuits", "experiments"],
        skills=["circuit reasoning", "fine taping", "troubleshooting"],
        materials=["copper tape", "coin cell battery", "LED stickers or through-hole LEDs", "card stock"],
        thinking=["causal reasoning", "debugging by isolation"],
        access=["Small parts and a choking hazard from coin cells; supervise children closely", "Vision-friendly if LEDs and tape are large; magnification helps"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour for a first light-up card",
        difficulty="beginner",
    ),
    _i(
        slug="crystal-growing",
        title="Crystal Growing",
        category="Science & Everyday Experiments",
        short="Growing crystals from saturated solutions and observing how structure emerges.",
        long=(
            "Crystal growing dissolves a salt or mineral in hot water, lets it cool saturated, and "
            "waits as ordered structures emerge. Salt, sugar, and alum are common beginner materials. "
            "The practice teaches supersaturation, nucleation, and patience, and results are "
            "genuinely beautiful. Time-lapse photography pairs well with it."
        ),
        step="Grow alum crystals on a string in a supersaturated solution and photograph them daily.",
        tags=["crystals", "chemistry", "growth", "patience"],
        skills=["making saturated solutions", "observation over days", "recording growth"],
        materials=["alum or salt", "hot water", "jar", "string and pencil", "thermometer (optional)"],
        thinking=["ordered structure from chaos", "long observation"],
        access=["Hot water needs care; adult supervision for children", "Seated bench work"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Setup an hour; growth over days to weeks",
        difficulty="beginner",
    ),
    _i(
        slug="kitchen-chemistry",
        title="Kitchen Chemistry",
        category="Science & Everyday Experiments",
        short="Exploring real chemistry through cooking and household materials.",
        long=(
            "Kitchen chemistry investigates the science in ordinary cooking and household "
            "materials — acids and bases, emulsions, Maillard browning, and crystallisation. "
            "Experiments are safe, cheap, and directly observable. Beginners learn to design a "
            "simple comparison, changing one variable and recording what happens."
        ),
        step="Test three household liquids with baking soda to see which are acids, recording your predictions first.",
        tags=["chemistry", "kitchen", "experiments", "science"],
        skills=["hypothesis design", "controlled comparison", "observation"],
        materials=["household ingredients", "notebook", "simple measures"],
        thinking=["predict-then-test discipline", "variable control"],
        access=["Seated kitchen work; adapt for various mobility levels", "Normal kitchen safety applies"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Half an hour per experiment",
        difficulty="beginner",
    ),
    _i(
        slug="magnetism-play",
        title="Magnetism Play",
        category="Science & Everyday Experiments",
        short="Exploring magnetic fields and forces with magnets, filings, and simple experiments.",
        long=(
            "Magnetism play explores fields and forces with everyday magnets. Iron filings map field "
            "lines, compasses show direction, and stacking magnets changes strength. It is one of "
            "the most tactile branches of physics, and cheap to explore. Beginners learn to predict "
            "before testing, which turns play into experiment."
        ),
        step="Map a bar magnet's field with iron filings on paper, then predict before testing a second magnet's effect.",
        tags=["magnetism", "physics", "fields", "play"],
        skills=["predicting outcomes", "field visualisation", "systematic testing"],
        materials=["bar and disc magnets", "iron filings", "compass", "paper"],
        thinking=["invisible forces made visible", "prediction discipline"],
        access=["Seated table work; large magnets are easier to handle", "Keep small magnets away from children"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Half an hour",
        difficulty="beginner",
    ),
    # --- Community & Craft ---------------------------------------------------
    _i(
        slug="community-kitchens",
        title="Community Kitchens",
        category="Community & Craft",
        short="Cooking together in shared spaces to feed people and share skills.",
        long=(
            "Community kitchens are shared cooking spaces run for participants rather than "
            "customers. People cook in batches, split tasks, and share the meal. The skills are "
            "practical — bulk prep, safe handling, working in a team — and the social benefit is "
            "part of the point. Many are volunteer-run and welcome new hands."
        ),
        step="Find a local community kitchen or cooking group and attend one session as a helper.",
        tags=["cooking", "community", "sharing", "volunteering"],
        skills=["bulk preparation", "teamwork in a kitchen", "food safety awareness"],
        materials=["an apron", "a knife (optional)", "willingness to take direction"],
        thinking=["cooperation at scale", "service as participation"],
        access=["Kitchens vary; ask about seating tasks and step-free access", "Physical tasks can often be swapped"],
        solo=["group"],
        modes=["in_person"],
        time="A session of a few hours",
        difficulty="beginner",
    ),
    _i(
        slug="citizen-science",
        title="Citizen Science",
        category="Community & Craft",
        short="Contributing to real research by recording observations — wildlife, weather, galaxies.",
        long=(
            "Citizen science projects use volunteers to gather or classify data at a scale "
            "professionals alone could not reach. Projects range from counting birds to "
            "transcribing old ship logs. Beginners pick a project with a clear protocol and short "
            "tasks. The work is real and citable, which surprises many newcomers."
        ),
        step="Join one established citizen-science project and complete its first training module and task.",
        tags=["research", "community", "data", "contribution"],
        skills=["following protocols", "accurate recording", "classification"],
        materials=["phone or computer", "an account with a project", "patience for repetition"],
        thinking=["small contributions compounding", "protocol fidelity"],
        access=["Many projects are fully remote and screen-reader friendly", "Tasks vary from minutes to hours"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="Minutes to hours, self-scheduled",
        difficulty="beginner",
    ),
    _i(
        slug="oral-history",
        title="Oral History",
        category="Community & Craft",
        short="Recording people's spoken memories and experiences, with consent and care.",
        long=(
            "Oral history records people's accounts of their lives and experiences on audio or "
            "video. It combines interviewing skill with ethics: consent, context, and the "
            "responsibility of holding someone's story. Beginners learn question technique and "
            "recording basics, then deposit or share recordings appropriately. The value grows "
            "over decades."
        ),
        step="With consent, record a fifteen-minute conversation with an older relative about one specific period of their life.",
        tags=["interviewing", "recording", "memory", "archive"],
        skills=["question technique", "audio recording", "ethical consent"],
        materials=["recorder or phone", "external microphone (optional)", "consent form", "notebook"],
        thinking=["listening without steering", "stewardship of others' stories"],
        access=["Can be done seated; remote recording tools exist", "Consent processes should be clear and repeatable"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour per interview plus preparation",
        difficulty="beginner",
    ),
    _i(
        slug="neighbourhood-mapping",
        title="Neighbourhood Mapping",
        category="Community & Craft",
        short="Drawing maps of your local area from direct observation — trees, benches, crossings.",
        long=(
            "Neighbourhood mapping records a local area through your own observation, on foot or "
            "from memory. Themes might be shade, safety, play spaces, or small wildlife. The maps "
            "are useful to communities and councils, and they sharpen how you read your own street. "
            "Paper and a clipboard are enough."
        ),
        step="Walk one street and map every tree and bench you pass, then look at what the map reveals.",
        tags=["maps", "walking", "observation", "community"],
        skills=["spatial recording", "noticing infrastructure", "simplifying detail"],
        materials=["paper or a simple mapping app", "pen", "clipboard"],
        thinking=["place as data", "seeing what is missing"],
        access=["Routes can be chosen for step-free access; mapping can also be done from memory", "Seated drawing afterwards"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour per map",
        difficulty="beginner",
    ),
    _i(
        slug="community-gardening",
        title="Community Gardening",
        category="Community & Craft",
        short="Growing food and flowers together on shared land, and sharing the harvest.",
        long=(
            "Community gardens are plots tended collectively, often with shared tools and harvests. "
            "The work is real gardening — beds, compost, watering rotas — done alongside neighbours. "
            "Beginners learn by taking a small defined job and showing up consistently. Many gardens "
            "have raised beds and accessible paths."
        ),
        step="Find a local community garden and volunteer for one session, taking the smallest defined task.",
        tags=["gardening", "community", "food", "sharing"],
        skills=["seasonal growing", "shared tool use", "reliable contribution"],
        materials=["gardening gloves", "weather-appropriate clothes", "water bottle"],
        thinking=["shared stewardship", "contributing to a commons"],
        access=["Many have raised beds and step-free paths; ask about accessible roles", "Tasks range from light to heavy"],
        solo=["group"],
        modes=["in_person"],
        time="A session of a few hours weekly",
        difficulty="beginner",
    ),
    _i(
        slug="quilting-circles",
        title="Quilting Circles",
        category="Community & Craft",
        short="Sewing quilts, often in groups, combining blocks, layering, and stitching.",
        long=(
            "Quilting joins layers of fabric with stitches, usually in a group where blocks are "
            "sewn together and the top is layered and quilted. Beginners learn simple piecing and "
            "the collaborative rhythm of a circle. Circles often welcome borrowed skills — pressing, "
            "cutting, and binding are all useful contributions."
        ),
        step="Join a circle session and contribute one simple block or help press and cut fabric.",
        tags=["textiles", "sewing", "community", "quilts"],
        skills=["piecing", "precise cutting", "hand or machine quilting"],
        materials=["fabric scraps", "needle or machine", "thread", "rotary cutter or scissors"],
        thinking=["modular assembly", "contributing a piece to a whole"],
        access=["Seated work; machines and tools can be adapted", "Circles often meet in step-free venues"],
        solo=["group"],
        modes=["online", "in_person"],
        time="Sessions of a few hours over weeks",
        difficulty="beginner",
        notes="Quilting circles exist in many cultural traditions; this entry describes the general communal practice.",
    ),
    _i(
        slug="tool-lending-libraries",
        title="Tool-Lending Libraries",
        category="Community & Craft",
        short="Borrowing tools from a shared library instead of buying, and learning to use them.",
        long=(
            "Tool-lending libraries lend equipment that people rarely need to own — power drills, "
            "carpet cleaners, tile saws. Using one turns a purchase decision into a simple loan, "
            "and staff often teach basic use. The model reduces waste and cost, and many are run "
            "by local libraries or community centres."
        ),
        step="Find a tool-lending library, join it, and borrow one tool for a household job.",
        tags=["tools", "sharing", "household", "sustainability"],
        skills=["tool selection", "safe use", "borrowing logistics"],
        materials=["membership", "a job that needs a tool", "transport for larger items"],
        thinking=["access over ownership", "asking for instruction"],
        access=["Many are in accessible libraries; home delivery sometimes exists", "Staff can advise on manageable tools"],
        solo=["solo", "group"],
        modes=["in_person"],
        time="Minutes to borrow; the job's length to use",
        difficulty="beginner",
    ),
    _i(
        slug="skill-share-workshops",
        title="Skill-Share Workshops",
        category="Community & Craft",
        short="Teaching and learning informally in swaps where everyone brings and takes a skill.",
        long=(
            "Skill-share workshops are informal sessions where participants teach each other "
            "something rather than hiring experts. Anyone can offer a skill — darning, budgeting, "
            "a language basics — and learn another. The practice builds confidence in both "
            "teaching and learning, and it costs nothing but preparation."
        ),
        step="Offer one simple skill in a local or online skill swap, and take someone else's in return.",
        tags=["teaching", "community", "sharing", "workshop"],
        skills=["explaining clearly", "learning from peers", "session planning"],
        materials=["a skill to teach", "simple materials", "a group or forum"],
        thinking=["everyone as teacher and learner", "lowering the stakes"],
        access=["Online swaps are fully remote; in-person venues should be step-free", "Topics can suit any ability"],
        solo=["group"],
        modes=["online", "in_person"],
        time="An hour or two per swap",
        difficulty="beginner",
    ),
    _i(
        slug="local-history-walks",
        title="Local History Walks",
        category="Community & Craft",
        short="Walking a neighbourhood with a historical lens, reading buildings and street names.",
        long=(
            "Local history walks read a place for its past: buildings, street names, old industry, "
            "and changed landscapes. You can join a guided group or lead your own using archives "
            "and maps. The skill is looking at what is in front of you and asking what came before. "
            "Old and new maps side by side are the single best tool."
        ),
        step="Walk one street with an old map on your phone and find three things that have changed.",
        tags=["history", "walking", "place", "archives"],
        skills=["reading buildings", "comparing maps", "archival searching"],
        materials=["walking shoes", "phone with old maps", "notebook"],
        thinking=["layers of time", "evidence in the built environment"],
        access=["Choose step-free routes; much can also be done from a chair with map archives", "Guided walks vary in length"],
        solo=["solo", "group"],
        modes=["online", "in_person"],
        time="An hour or two",
        difficulty="beginner",
    ),
]


EDGES: list[tuple[str, str, str, str | None]] = [
    # Creative Practices
    ("bookbinding", "linocut-printmaking", "shares_technique", "both rely on precise folding and registration"),
    ("bookbinding", "pop-up-paper-engineering", "prerequisite_for", "folding and scoring skills transfer directly"),
    ("bookbinding", "cut-paper-collage", "shares_material", "both start from paper and scissors"),
    ("bookbinding", "herbarium-plant-pressing", "complementary_activity", "pressed specimens are often mounted into hand-made books"),
    ("linocut-printmaking", "cyanotype-printing", "shares_way_of_thinking", "both build repeatable images from a prepared matrix"),
    ("linocut-printmaking", "cut-paper-collage", "shares_technique", "both cut shapes to build a composition"),
    ("cyanotype-printing", "natural-dyeing", "shares_material", "both use chemistry to colour fibre and paper"),
    ("cut-paper-collage", "pop-up-paper-engineering", "shares_material", "both build forms from card and paper"),
    ("stop-motion-animation", "miniature-making", "complementary_activity", "miniatures are commonly the subjects of stop-motion films"),
    ("stop-motion-animation", "sound-design", "complementary_activity", "animated films need designed sound"),
    ("natural-dyeing", "visible-mending", "complementary_activity", "dyed thread and cloth are often used in mending"),
    ("natural-dyeing", "sashiko-stitching", "related_culture_or_context", "indigo-dyed cloth is a traditional ground for sashiko"),
    ("origami", "pop-up-paper-engineering", "shares_way_of_thinking", "both reason about folds in three dimensions"),
    ("origami", "bookbinding", "shares_technique", "both depend on crisp, accurate folds"),
    ("urban-sketching", "data-storytelling", "shares_skill", "both simplify what is in front of you into a readable form"),
    ("urban-sketching", "neighbourhood-mapping", "complementary_activity", "sketching and mapping both record a place closely"),
    ("urban-sketching", "cut-paper-collage", "shares_way_of_thinking", "both compose from observed shapes"),
    ("linocut-printmaking", "poster-composition", "complementary_activity", "printed images often become posters"),
    ("bookbinding", "bird-journaling", "complementary_activity", "a hand-made notebook suits field journaling"),
    ("pop-up-paper-engineering", "puzzle-design", "shares_way_of_thinking", "both design mechanical reveals"),
    ("cut-paper-collage", "icon-design", "shares_way_of_thinking", "both abstract meaning into flat shapes"),
    ("colour-theory", "cyanotype-printing", "shares_way_of_thinking", "both work within a constrained palette"),
    ("colour-theory", "natural-dyeing", "complementary_activity", "understanding colour helps plan dye results"),
    ("colour-theory", "poster-composition", "prerequisite_for", "palette decisions underpin poster hierarchy"),
    ("layout-and-grids", "typography-basics", "shares_way_of_thinking", "both impose structure on readable text"),
    ("layout-and-grids", "poster-composition", "prerequisite_for", "grids are the skeleton of a poster"),
    ("typography-basics", "poster-composition", "shares_skill", "both depend on type hierarchy at scale"),
    ("typography-basics", "information-design", "shares_skill", "both make text usable through arrangement"),
    ("information-design", "accessible-design-thinking", "complementary_activity", "usable information must also be accessible"),
    ("information-design", "data-storytelling", "shares_skill", "both structure evidence for a reader"),
    ("data-storytelling", "sketchnoting", "shares_skill", "both distil information into a visual form"),
    ("sketchnoting", "urban-sketching", "shares_skill", "both draw quickly from life"),
    ("icon-design", "layout-and-grids", "shares_way_of_thinking", "both rely on a consistent underlying grid"),
    ("icon-design", "accessible-design-thinking", "complementary_activity", "legible icons are a core accessibility concern"),
    ("accessible-design-thinking", "information-design", "complementary_activity", "designing for range improves clarity for everyone"),
    # Making & Repair
    ("visible-mending", "sashiko-stitching", "shares_technique", "both use rows of running stitch to reinforce cloth"),
    ("visible-mending", "quilting-circles", "shares_skill", "both use layered stitching over fabric"),
    ("basketry", "recycled-sculpture", "shares_way_of_thinking", "both build structure by weaving or binding strips"),
    ("basketry", "herbarium-plant-pressing", "shares_material", "both work with dried plant material"),
    ("clay-modelling", "crystal-growing", "shares_way_of_thinking", "both grow structure slowly over time"),
    ("miniature-making", "escape-room-design", "complementary_activity", "miniature props suit small escape-room puzzles"),
    ("furniture-repair", "bicycle-maintenance", "shares_skill", "both use basic workshop tools and diagnosis"),
    ("furniture-repair", "wood-spoon-carving", "shares_material", "both work with wood and hand tools"),
    ("wood-spoon-carving", "basketry", "shares_way_of_thinking", "both shape natural materials by hand"),
    ("recycled-sculpture", "diy-instrument-making", "shares_material", "both build from discarded household materials"),
    ("visible-mending", "clay-modelling", "shares_way_of_thinking", "both value repair and imperfection over newness"),
    ("bicycle-maintenance", "tool-lending-libraries", "complementary_activity", "specialist bike tools can be borrowed rather than owned"),
    ("furniture-repair", "tool-lending-libraries", "complementary_activity", "power tools for repair jobs can be borrowed"),
    ("wood-spoon-carving", "skill-share-workshops", "complementary_activity", "carving is a common skill-swap topic"),
    ("miniature-making", "clay-modelling", "shares_technique", "both shape small forms by hand"),
    # Nature & Living Systems
    ("seed-saving", "balcony-gardening", "complementary_activity", "saved seed is sown in next season's containers"),
    ("balcony-gardening", "pollinator-gardening", "complementary_activity", "flowering pots support urban pollinators"),
    ("compost-science", "balcony-gardening", "complementary_activity", "compost feeds container plants"),
    ("compost-science", "community-gardening", "complementary_activity", "community gardens usually run compost systems"),
    ("mushroom-observation", "tree-identification", "shares_skill", "both identify species by close observation"),
    ("bird-journaling", "tree-identification", "complementary_activity", "habitat knowledge improves birding"),
    ("bird-journaling", "local-history-walks", "shares_way_of_thinking", "both build records from walking a place"),
    ("pollinator-gardening", "balcony-gardening", "complementary_activity", "a window box can be a pollinator patch"),
    ("freshwater-pond-study", "citizen-science", "complementary_activity", "pond surveys feed community recording projects"),
    ("herbarium-plant-pressing", "tree-identification", "complementary_activity", "pressed specimens support identification"),
    ("seed-saving", "community-gardening", "complementary_activity", "seed is often shared across a community garden"),
    ("mushroom-observation", "freshwater-pond-study", "shares_way_of_thinking", "both are careful surveys of small life"),
    ("compost-science", "kitchen-chemistry", "shares_way_of_thinking", "both are applied chemistry of organic material"),
    ("weather-journaling", "cloud-spotting", "prerequisite_for", "cloud reading feeds a wider weather record"),
    ("bird-journaling", "citizen-science", "complementary_activity", "bird records are a classic citizen-science contribution"),
    ("tree-identification", "pollinator-gardening", "shares_skill", "plant knowledge guides pollinator planting"),
    # Movement & Play
    ("orienteering", "nordic-walking", "complementary_activity", "poles make longer navigation courses easier"),
    ("juggling", "beatboxing", "shares_way_of_thinking", "both build skills from layered rhythmic repetition"),
    ("jump-rope-skills", "hand-percussion", "shares_skill", "both depend on steady rhythm"),
    ("slacklining", "indoor-bouldering", "shares_skill", "both train balance and body awareness"),
    ("slacklining", "improvisational-dance", "shares_way_of_thinking", "both respond continuously to instability"),
    ("hula-hooping", "jump-rope-skills", "shares_skill", "both are rhythmic coordination practices"),
    ("indoor-bouldering", "orienteering", "complementary_activity", "outdoor climbers often navigate to reach routes"),
    ("improvisational-dance", "improv-games", "shares_way_of_thinking", "both are built on accept-and-build spontaneity"),
    ("nordic-walking", "orienteering", "complementary_activity", "walking poles suit long navigation routes"),
    ("juggling", "hand-percussion", "shares_skill", "both train hand timing"),
    ("improvisational-dance", "choir-singing", "shares_way_of_thinking", "both are group practices of listening and response"),
    ("jump-rope-skills", "relative-pitch-training", "shares_way_of_thinking", "both are short, daily coordination practices"),
    # Music & Sound
    ("field-recording", "sound-design", "prerequisite_for", "recorded audio is the raw material of sound design"),
    ("diy-instrument-making", "magnetism-play", "shares_way_of_thinking", "both explore how physical properties shape an outcome"),
    ("modular-synthesis", "sound-design", "complementary_activity", "synthesis shapes textures for sound design"),
    ("beatboxing", "hand-percussion", "shares_way_of_thinking", "both are body-based rhythm making"),
    ("songwriting", "choir-singing", "complementary_activity", "songs are what choirs sing"),
    ("songwriting", "relative-pitch-training", "prerequisite_for", "ear training supports melodic writing"),
    ("relative-pitch-training", "choir-singing", "complementary_activity", "singing in harmony relies on relative pitch"),
    ("field-recording", "bird-journaling", "complementary_activity", "sound recording captures birdsong evidence"),
    ("sound-design", "stop-motion-animation", "complementary_activity", "animation needs a designed soundtrack"),
    ("diy-instrument-making", "hand-percussion", "complementary_activity", "hand drums are often the first homemade instruments"),
    ("beatboxing", "jump-rope-skills", "shares_way_of_thinking", "both are rhythm practices buildable in short sessions"),
    ("modular-synthesis", "simple-electronics", "shares_way_of_thinking", "both reason about signal flow through components"),
    # Food & Culture
    ("vegetable-fermentation", "home-pickling", "shares_technique", "both preserve vegetables in an acidic or brined environment"),
    ("vegetable-fermentation", "sourdough-bread", "shares_way_of_thinking", "both manage a living microbial process"),
    ("sourdough-bread", "jam-preserving", "shares_skill", "both are precise about ratios and setting points"),
    ("spice-blending", "seasonal-cooking", "complementary_activity", "blends season what is currently abundant"),
    ("coffee-brewing", "tea-brewing", "shares_way_of_thinking", "both are studies of extraction variables"),
    ("dumpling-folding", "skill-share-workshops", "complementary_activity", "folding techniques travel well as taught skills"),
    ("dumpling-folding", "sourdough-bread", "shares_skill", "both involve handling and shaping dough"),
    ("home-pickling", "seasonal-cooking", "complementary_activity", "pickling uses up seasonal gluts"),
    ("jam-preserving", "seasonal-cooking", "complementary_activity", "preserving follows the fruit season"),
    ("spice-blending", "coffee-brewing", "shares_way_of_thinking", "both balance flavour by adjusting proportions"),
    ("tea-brewing", "vegetable-fermentation", "related_culture_or_context", "many fermented drinks and teas share brewing traditions"),
    ("seasonal-cooking", "community-kitchens", "complementary_activity", "bulk seasonal cooking suits shared kitchens"),
    # Games & Strategy
    ("chess-variants", "go", "shares_skill", "both are territory and position games"),
    ("mechanical-puzzle-solving", "puzzle-design", "shares_way_of_thinking", "solving teaches how designers hide solutions"),
    ("puzzle-design", "escape-room-design", "prerequisite_for", "escape rooms are built from chained puzzles"),
    ("card-game-design", "puzzle-design", "shares_skill", "both are rule design refined by playtesting"),
    ("cooperative-board-games", "improv-games", "complementary_activity", "both are social practices of shared decision-making"),
    ("improv-games", "skill-share-workshops", "complementary_activity", "improv exercises are common warm-ups in workshops"),
    ("escape-room-design", "card-game-design", "shares_way_of_thinking", "both design timed, rule-bound experiences"),
    ("go", "mechanical-puzzle-solving", "shares_way_of_thinking", "both reward patient pattern recognition"),
    ("chess-variants", "card-game-design", "shares_skill", "both involve balancing asymmetric options"),
    ("escape-room-design", "puzzle-design", "prerequisite_for", "puzzle chaining is the core of escape-room design"),
    # Science & Everyday Experiments
    ("backyard-astronomy", "cloud-spotting", "complementary_activity", "cloud cover decides whether astronomy is possible"),
    ("amateur-microscopy", "freshwater-pond-study", "complementary_activity", "microscopy identifies pond invertebrates"),
    ("weather-journaling", "citizen-science", "complementary_activity", "personal records can feed weather networks"),
    ("simple-electronics", "paper-circuits", "prerequisite_for", "circuit basics transfer directly onto paper"),
    ("crystal-growing", "kitchen-chemistry", "shares_material", "both use common salts and kitchen chemistry"),
    ("magnetism-play", "simple-electronics", "shares_way_of_thinking", "both explore invisible physical forces"),
    ("paper-circuits", "diy-instrument-making", "shares_material", "both use simple household electronics and craft"),
    ("amateur-microscopy", "herbarium-plant-pressing", "complementary_activity", "pressed plants are useful microscope specimens"),
    ("cloud-spotting", "field-recording", "complementary_activity", "weather conditions shape the soundscape"),
    ("crystal-growing", "natural-dyeing", "shares_way_of_thinking", "both grow and fix ordered structures through chemistry"),
    ("kitchen-chemistry", "vegetable-fermentation", "shares_way_of_thinking", "fermentation is applied food chemistry"),
    ("magnetism-play", "diy-instrument-making", "shares_material", "magnets appear in homemade instruments and sensors"),
    # Community & Craft
    ("community-kitchens", "seasonal-cooking", "complementary_activity", "shared kitchens cook what is in season"),
    ("community-gardening", "seed-saving", "complementary_activity", "seed is saved and shared across plots"),
    ("community-gardening", "pollinator-gardening", "complementary_activity", "community plots often include pollinator strips"),
    ("oral-history", "local-history-walks", "complementary_activity", "walks and interviews both record a place's past"),
    ("neighbourhood-mapping", "local-history-walks", "shares_skill", "both read a place closely and record it"),
    ("neighbourhood-mapping", "citizen-science", "complementary_activity", "local mapping can contribute to civic data"),
    ("tool-lending-libraries", "skill-share-workshops", "complementary_activity", "borrowed tools often accompany taught skills"),
    ("quilting-circles", "visible-mending", "shares_skill", "both are group needlework traditions"),
    ("skill-share-workshops", "community-kitchens", "complementary_activity", "cooking is a common skill-swap subject"),
    ("quilting-circles", "natural-dyeing", "complementary_activity", "dyed fabric is a prized quilting material"),
    ("oral-history", "citizen-science", "shares_way_of_thinking", "both are structured recording by volunteers"),
    ("community-gardening", "compost-science", "complementary_activity", "shared gardens run compost systems"),
    ("local-history-walks", "bird-journaling", "shares_way_of_thinking", "both are close observations of a walked place"),

    # Coverage edges: every entry participates in at least two relationships.
    ("backyard-astronomy", "amateur-microscopy", "contrasts_with", "one looks impossibly far away, the other impossibly close"),
    ("backyard-astronomy", "weather-journaling", "complementary_activity", "clear-sky records guide when to observe"),
    ("cooperative-board-games", "chess-variants", "contrasts_with", "shared goals against the game versus direct opposition"),
    ("cooperative-board-games", "card-game-design", "complementary_activity", "designing cooperation is a distinct card-game challenge"),
    ("hula-hooping", "nordic-walking", "contrasts_with", "circular rhythm versus linear distance"),
    ("hula-hooping", "indoor-bouldering", "complementary_activity", "hooping warms up core and shoulders before climbing"),
    ("pollinator-gardening", "community-gardening", "shares_way_of_thinking", "both plan planting as an ecosystem rather than a display"),
    ("pollinator-gardening", "mushroom-observation", "complementary_activity", "flowering habitat and fungi mark the same healthy patch"),
    ("indoor-bouldering", "slacklining", "contrasts_with", "committed grips on fixed holds versus constant correction on a moving line"),
    ("indoor-bouldering", "jump-rope-skills", "complementary_activity", "footwork and rhythm training carry between the two"),
    ("vegetable-fermentation", "kitchen-chemistry", "shares_way_of_thinking", "both treat the kitchen as a controlled experiment"),
    ("go", "chess-variants", "contrasts_with", "quiet territorial accumulation versus tactical material fighting"),
    ("information-design", "icon-design", "prerequisite_for", "layout and hierarchy discipline precede symbol design"),
    ("field-recording", "modular-synthesis", "complementary_activity", "recorded sound is often the raw material fed into synthesis"),
]
