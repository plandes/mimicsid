# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]


## [1.2.0] - 2023-06-09
### Added
- CLI summary output format.

### Changed
- Model training and automation process.
- Upgraded to [zensols.mimic] 1.2.0.
- Remove `PredictedSection` and switch to its super class.


## [1.1.0] - 2023-04-05
### Added
- Automatically predict sections for note missing section annotations.
- Output formatting added to raw notes.
- More model training and packaging automation.

### Changed
- Fixed slow hospital admission persistence when persisting predicted notes.
- Fix `AgeType` enumeration typo.
- Upgraded [zensols.deepnlp] to 1.8.0.
- Upgraded [zensols.mimic] to 1.1.0.


## [1.0.0] - 2023-02-10
### Changed
- Upgraded [zensols.deepnlp] to 1.7.0.
- Upgraded [zensols.mimic] to 1.0.0.


## [0.0.1] - 2022-06-22
### Added
- Initial version.


<!-- links -->
[Unreleased]: https://github.com/plandes/mimicsid/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/plandes/mimicsid/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/plandes/mimicsid/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/plandes/mimicsid/compare/v0.0.1...v1.0.0
[0.0.1]: https://github.com/plandes/mimicsid/compare/v0.0.0...v0.0.1

[zensols.deepnlp]: https://github.com/plandes/deepnlp
[zensols.mimic]: https://github.com/plandes/mimic
