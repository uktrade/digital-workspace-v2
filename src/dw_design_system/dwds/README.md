# Digital Workspace design system

A basic and simple design system for Digital Workspace content.

## Overall approach

The design system is intended to have no external dependencies and to be both simple and pragmatic.

The Components are intended to be CSS and HTML and optionally presented to content editors via
StreamBlocks; the Python, HTML and SCSS files are colocated in the same directory for ease of use.

Elements are for shared HTML/CSS interface elements; these are not intended to be exposed outside
the component library or used more widely.

A component is a top level interface element that has the same meaning in visual design as in
technical implementation.

We are using modern, clean CSS and markup with an emphasis on simplicity, semantics, accessibility
and pragmatism. Components should have a simple and guessable API, based on flexible use cases.

## Visual design

Overall visual structures and hierarchies are loosely based on GDS and extended from there, but
this does not extend to implementation.

## CSS

Minimal CSS is the watchword, using techniques from [Every Layout](https://every-layout.dev) as
appropriate, and minimal, simple styling wherever possible.

Root nodes of each component should be given a class with the `dwds-` prefix, and no other nodes
should have class or identifiers attached unless necessary; sub-component elements should pick up
styling as being children of the root node, wherever possible.

## Markup

HTML markup should be semantic and accessible, with minimal DOM nodes.
