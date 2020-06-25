

Unser Annotationsstandard basiert auf den folgenden Überlegungen:

1. Wir möchten reguläre Zeitbegriffe erkennen.

    - Tag: `<TIMEX3 />`

    - Generell gelten die Standards zur TimeML-Annotation in verschiedenen Sprachen
    - Nützliche Hinweise, bzw. notwendige Teilabweichungen vom Standard:
        - Daten vor Chr. werden mit "BC" im "value"-Attribut gepräfixt, also etwa "BC0200"
        - Unbekannte Daten mit einem festen Wert werden mit "X" abkürzt. Also etwa: "Einige Jahre später" ist eine DURATION mit dem Wert "PXY". Aber "Die sechsziger Jahre" ist ein DATE mit dem Wert "196" (_nicht_ "196X"), da hier das Datum entsprechend klar auf der 10er-Skala definiert ist.

1. Wir möchten Zeitbegriffe erkennen, die von besonderer theoretischer Relevanz für die archäologische Forschung sind. Dazu gehören insbesondere _Epochenbegriffe aller Art_

    - Tag: `<temponym />`
    - Temponyme werden generell bevorzugt vergeben. So ist "ionisch" in "eine ionische Vase" (fiktives Beispiel) ein Temponym vom Typ `material-culture` und kein Verweis auf die Provinz Ionien. Wird das Adjektiv hingegen nominalisiert benutzt, um eine Person oder eine Gruppe von Personen zu bezeichnen, wie in "ein Ionier", dann handelt es sich um eine NE vom Typ `person-group`. Dadurch wird sichergestellt, dass die verschiedenen Verwendungen des Konzepts später weiterhin erkennbar sind und unterschieden werden können.
    - Die Herkunft eines Temponym-Begriffs kann genauso entscheidend sein wie sein Bezug, um das entsprechende Attribut zu vergeben. So kann "preistorici" in "su luoghi preistorici" sowohl kulturell gemeint sein (Orte vor dem Beginn der Niederschrift von Geschichte), aber auch materiell-kulturell, insofern materielle Zeugnisse von Orten gemeint sind. Hier ist nach dem Kontext zu entscheiden, welche Verwendung überwiegt.
    - Grenzfälle: In "una fase successiva di occupazione islamica" ist "islamica" nicht der Name für die "fase", sondern eine Beschreibung, daher keine Benennung im eigentlichen Sinne. Es geht also immer trotzdem um Namen im eigentlichen Sinne.

2. Wir möchten wissen, worauf sich ein Epochenbegriff bezieht, wenn er Teil einer Nominalphrase ist.

    - Tag: `<temponym-phrase />`

    - Eine Temponym-Phrase kann mehrere Temponyme enthalten: "los años del fascismo y de la posguerra"
    - Eine Temponym-Phrase sollte den Artikel enthalten, wenn einer vorhanden ist. Zur Kompatibilität mit TIMEX3-tags in TimeML sollte jedoch der Artikel nicht mit einzogen werden, wenn er Teil einer Präposition ist. So wird das "ai" in "ai paleo-ambienti naturali" nicht als Teil der Temponym-Phrase gezählt, wohl aber das "i" in "i cimiteri cristiani".
    - Einschlägig sind entsprechend die Vorgaben zur Behandlung von TIMEX3-Tags in den einzelnen Annotationsstandards für die verschiedenen Korpus-Sprachen.
    - Wenn die temponym-Phrase mit dem Temponym übereinstimmt, wird kein Tag vergeben
    - Steht ein Temponym in Klammern, z.B. "(XXX dinastia)", dann bildet der Klammerausdurck die Temponym-Phrase, das Temponym enthält die Klammern nicht.
    - Der Typ einse Temponyms wird bevorzugt anhand der Wortart bestimmt (z.B. ist eine "Dynastie" eigentlich immer eine politisch-historisches und kein materielle-kulturelles Temponym, da es auf eine Herrscherfamilie anspielt), bei Unklarheiten kann aber auch der Kontext entscheidend sein. Die "späte ägyptische Epoche" kann kulturell verstanden werden oder bezogen auf die politische Situation.


3. Eventuell möchten wir später auch andere benannte Entitäten erkennen, die datiert werden können. Dazu gehören besonders Personennamen, Ereignisse, aber möglicherweise auch Orte

    - Tag: `<dne type="person" />`
    - Tag: `<dne type="event" />`
    - Tag: `<dne type="location" />`
    - Tag: `<dne type="organization" />`

    - Annotiert werden sollten nur _benannte_ Entitäten.
        - In "bahía de Nápoles" ist nur "Nápoles" zu annotieren, in "i Tre Laghi del Giura" jedoch der gesamte Ausdruck, weil "Tre Laghi" nur den ersten Teil des Namens bildet. (Hier leicht an der Großschreibung zu erkennen.)
        - Ist ein Personenname durch ein Amt gegeben, das nicht allgemein zu verstehen ist, so wird die Nennung ebenfalls annotiert: Also "Gouverneur Général" wird getagged, wenn es sich auf eine bestimmte Person bezieht, nicht jedoch wenn allgemein von Menschen diesen Amtes die Rede ist.
    - Nicht im Sinne eines Namens verwendete Bezüge auf NEs sind nicht zu annotieren, z.B. nicht "la erupción", wohl aber "la erupción del Vesubio", selbst wenn beidesmal erstere gemeint ist.
    - NEs können verschachtelt sein. "University of Valladolid" enthält einen Ort und ist insgesmat eine Organisation.
    - NEs werden auch annotiert, wenn die Zuordnung adjektivisch ist, bspw. sind in "el ingeniero suizo Karl Weber" sowohl "Karl Weber" als auch "suizo" zu annotieren.
    - Wird ein (ggf. nominalisiertes) Adjektiv, das auf einen Ort verweist, jedoch benutzt, um eine Gruppe von Personen zu identifizieren, z.B. in "un Palmyrénien", dann wird das Attribut `type="person-group"` vergeben, nicht `location`
    - Namen für Schichten, bzw. stratigraphische Einheiten in Ausgrabungen werden zunächst als DNE vom Typ "other" notiert. (Unklar, ob wir die wirklich benötigen. Es sind aber benannte datierbare Entitäten.)

4. Wir möchten den Kontext von literarischen Verweisen vom sonstigen Fließtext trennen.

    - Tag: `<literature />`
    - Der Tag sollte verwendet werden, selbst wenn keine Zeitangabe in der Literaturangabe enthalten ist.
    - Stehen mehreren Literaturangaben sollte jede einzeln ausgezeichnet werden.


5. Wir möchten für alle oben genannten Entities und Zeitangaben unterscheiden, ob sie in den thematischen Kontext fallen oder ob sie zur Erkundungsgeschichte gehören. Da wir zur Zeit keine Archäologen zur Verfügung haben, möchten wir auch angeben können, dass wir uns in der Sache unsicher sind. Wir gehen zunächst davon aus, dass beide Kategorien sich ausschließen, dass also nicht-thematische Angaben immer zum Erkundungszusammenhang gehören.

    - Attribute: `temporal-context="[topic|exploration|unsure]"`
    - Im einfachsten Fall klar zu unterscheiden: Ist der Begriff modern oder antik?
        - "das am nördlichen Ende der Hochebene von _Kosovo_ gelegene _Municipium Dardanorum_" (Hier ist Kosove im Entdeckungskontext zu sehen und Municipium Dardanorum ist thematischer Kontext, also das, was eigentlich erforscht wird.)
    - Schwierig Fälle:
        - "Among these findings is also the so-called __Villa de los Papiros__, the famous and luxurious construction located on the outskirts of __Herculaneum__, to which the author will return later."
        - Obwohl der Satz mit "findings" beginnt, sind das Thema doch die Villa und der Ort selbst, also sind beide vom context `topic`. (Dass die Villa gefunden wird ist nicht im Vordergrund, sondern wird erwähnt.)
    - Informationen im Rahmen einer allgemeinen orts-geschichtlichen Einführung sind eher im "exploration"-Timeframe, z.B. dieser Satzanfang aus einem Buch, in dem es um die phönizische, karthagische und römische Gischichte von Iol-Caesarea-geht: "En 1531, Charles Quint […] voulut s'assurer un lieu de débarquement […]". Da die besprochene Zeit nicht die des eigentlichen Themas ist, zählt sie zum Exploration-Timeframe.
    - Ziel ist es, die Unterscheidung z.B. für die Disambiguierung von Begriffen, die sich sowohl auf die Erkundungs- als auch auf die thematische Zeit beziehen können, z.B. kann "roman" auf einen modernen wie auf einen antiken Römer Bezug nehmen.
    - Nicht immer eindeutig. Die Vergabe von `topic` kann generell bevozug geschehen, besonders bei Zeitausdrücken (TIMEX/TEMPONYM)
    - ABER: Die `topic`-Annotation sollte bei DNEs dann vergeben werden, wenn die entsprechende Entity einen Rückschluss auf die spezifisch besprochene Zeit erlaubt, also z.B. nicht für allgemeine und moderne Ortsbegriffe wie "Europa", "China" etc., wohl aber für historische Entitäten wie etwa "die Seidenstraße". Ebenso wird `topic` vergeben, wenn ein Fundplatz bezeichnet ist, der nicht auch gleichzeitig eine moderne Stadt benennt, so ist etwa der Fundort "Shilipubei" als `topic`, aber der nahe gelegene Ort "Shilipu" als `exploration` zu markieren.

6. Wir möchten keine Zeitausdrücke herausgreifen, die grob unpräzise sind. Zeitausdrücke, die ledigliche große Zeitspannen umfassen, aber eine klare fachliche Bedeutung haben, sollten hingegen annotiert werden (v.a. geologische Epochen.)

    - z.B. wird "antica" in "una cappella più antica" nicht als Temponym annotiert.
