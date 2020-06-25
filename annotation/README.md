

# Annotation

This directory gathers some files that were used during annotation of the pilot and project corpus.

The annotation guidelines collect decisions on what to annotate that were made in the pilot and preliminaray project corpus annotations.

The css and   annotation-shortcut files were used for annotation with the [Oxygen XML Editor](https://www.oxygenxml.com/) using its [Author Mode](https://www.oxygenxml.com/doc/versions/21.1/ug-editor/topics/author-editor.html).

To prepare a plain text document for tagging use the script `prepare_tagging.sh`, which will link the  `.css` and `.dtd` files and wrap each line in a `<sentence />`-tag. The css will then be picked up by Oxygen when you switch to the author mode.
