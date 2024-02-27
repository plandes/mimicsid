# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).


## [Unreleased]


## [1.6.0] - 2024-02-27
### Added
- Functionality to optionally add unclassified and/or non-empty sections in the
  prediction results (from `SectionPredictor`).

### Changed
- Upgrade to [zensols.mimic] 1.6.0.


## [1.5.1] - 2024-01-17
### Changed
- Fix [No section: 'medcat_status_move_update'] error.


## [1.5.0] - 2023-12-05
### Changed
- Upgrade to [zensols.mimic] version 1.5.0.

### Added
- Support for Python 3.11.

### Removed
- Support for Python 3.9.


## [1.4.3] - 2023-08-25
### Changed
- Model injection and assertion bug fixes.


## [1.4.2] - 2023-08-16
### Changed
- Inject model configuration to allow the SQLite connection manager with the
  model without any PostgreSQL drivers installed.


## [1.4.1] - 2023-08-16
### Changed
- Updated configuration to download model version 0.0.3.


## [1.4.0] - 2023-08-16
### Added
- Model training and packaging automation script for all models.

### Changed
- Model is downloaded and installed correctly using preemptive stash priming
  from the [zensols.mimic] library.
- Upgraded [zensols.mimic] 1.4.0 and [zensols.deepnlp] 1.8.0
- Handle carriage returns (`\r`) as a feature in the model.
- Fix headers and sections matching up by removing newline tokens on
  prediction.
- Retrain and default to highest performing models for model version 0.0.3.
- Remove `pt.` to `patient` token replacements.


## [1.3.1] - 2023-06-28
### Changed
- Dependencies to force correct versions of torch, numpy and scipy.


## [1.3.0] - 2023-06-20
### Changed
- Upgrade to [zensols.mimic] 1.3.0.


## [1.2.0] - 2023-06-09
### Added
- CLI summary output format.

### Changed
- Model training and automation process.
- Remove `PredictedSection` and switch to its super class.
- Upgraded to [zensols.deepnlp] 1.9.0.
- Upgraded to [zensols.mimic] 1.2.0.


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
[Unreleased]: https://github.com/plandes/mimicsid/compare/v1.6.0...HEAD
[1.6.0]: https://github.com/plandes/mimicsid/compare/v1.5.1...v1.6.0
[1.5.1]: https://github.com/plandes/mimicsid/compare/v1.5.0...v1.5.1
[1.5.0]: https://github.com/plandes/mimicsid/compare/v1.4.3...v1.5.0
[1.4.3]: https://github.com/plandes/mimicsid/compare/v1.4.2...v1.4.3
[1.4.2]: https://github.com/plandes/mimicsid/compare/v1.4.1...v1.4.2
[1.4.1]: https://github.com/plandes/mimicsid/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/plandes/mimicsid/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/plandes/mimicsid/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/plandes/mimicsid/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/plandes/mimicsid/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/plandes/mimicsid/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/plandes/mimicsid/compare/v0.0.1...v1.0.0
[0.0.1]: https://github.com/plandes/mimicsid/compare/v0.0.0...v0.0.1

[zensols.deepnlp]: https://github.com/plandes/deepnlp
[zensols.mimic]: https://github.com/plandes/mimic
[No section: 'medcat_status_move_update']: https://github.com/plandes/mimicsid/issues/2
