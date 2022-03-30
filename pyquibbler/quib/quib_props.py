from __future__ import annotations
import dataclasses
import functools
import pathlib
import warnings

from weakref import ReferenceType
from typing import Union, Optional, Set, Iterable

from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.quib.func_calling.quib_func_call import CachingOptions
from pyquibbler.assignment import AssignmentTemplate, create_assignment_template
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.file_syncing import SaveFormat, CannotSaveFunctionQuibsAsValueException, \
    SAVE_FORMAT_TO_FQUIB_SAVE_FORMAT, ResponseToFileNotDefined, FileNotDefinedException, SAVE_FORMAT_TO_FILE_EXT
from pyquibbler.quib.graphics import UpdateType
from pyquibbler.quib.types import FileAndLineNumber
from pyquibbler.quib.utils.miscellaneous import NoValue
from pyquibbler.utilities.file_path import PathWithHyperLink
from pyquibbler.utilities.input_validation_utils import validate_user_input, get_enum_by_str, \
    InvalidArgumentValueException

from pyquibbler import Quib


@dataclasses.dataclass
class PropertyOnlyDefinedWhenQuibConnected(PyQuibblerException):
    property_name: str

    def __str__(self):
        return f"Property {self.property_name} is only defined when props is quib-connected."


def _verify_quib_connection(func):
    @functools.wraps(func)
    def _wrapper(self, *args, **kwargs):
        if self._quib_ref is None:
            raise PropertyOnlyDefinedWhenQuibConnected(func.__name__)
        return func(self, *args, **kwargs)

    return _wrapper


_verify_func_definition_connection = _verify_quib_connection


class QuibProps:

    PROPERTIES_AND_IS_SETTABLE = (
        ('assigned_name', True),
        ('name', False),
        ('functional_representation', False),
        ('save_directory', True),
        ('actual_save_directory', False),
        ('save_format', True),
        ('actual_save_format', False),
        ('file_path', False),
        ('allow_overriding', True),
        ('assigned_quibs', True),
        ('assignment_template', True),
        ('caching', True),
        ('graphics_update_type', True),
    )

    def __init__(self, quib: Quib = None):
        self._assigned_name: Union[None, str] = None
        self._save_directory: Union[None, pathlib.Path] = None
        self._save_format: Union[None, SaveFormat] = None
        self._allow_overriding: bool = False
        self._assignment_template: Union[None, AssignmentTemplate] = None
        self._caching: CachingOptions = CachingOptions.AUTO
        self._graphics_update_type: Union[None, UpdateType] = None
        self._assigned_quibs: Optional[Set[Quib]] = None
        self._quib_ref: Optional[ReferenceType[Quib]] = None
        self.set_quib(quib)

    def set_quib(self, quib_weakref: Optional[ReferenceType[Quib]]):
        self._quib_ref = quib_weakref

    @property
    def _quib(self) -> Optional[Quib]:
        return self._quib_ref() if self._quib_ref else None

    @property
    def _func_definition(self) -> Optional[FuncDefinition]:
        return self._quib.handler.func_definition if self._quib_ref else None

    def on_project_directory_change(self):
        if not (self.save_directory is not None and self.save_directory.is_absolute()):
            self._on_file_name_changed()

    def _on_file_name_changed(self):
        if self._quib_ref:
            self._quib.handler.file_syncer.on_file_name_changed()

    @classmethod
    def from_(cls,
              assigned_name: Union[None, str] = NoValue,
              save_directory: Union[None, str, pathlib.Path] = NoValue,
              save_format: Union[None, str, SaveFormat] = NoValue,
              allow_overriding: bool = NoValue,
              assignment_template: Union[None, tuple, AssignmentTemplate] = NoValue,
              caching: Union[str, CachingOptions] = NoValue,
              graphics_update_type: Union[None, str] = NoValue,
              assigned_quibs: Set[Quib] = NoValue,
              ):

        self = cls()
        self.setp(
            assigned_name=assigned_name,
            save_directory=save_directory,
            save_format=save_format,
            allow_overriding=allow_overriding,
            assignment_template=assignment_template,
            caching=caching,
            graphics_update_type=graphics_update_type,
            assigned_quibs=assigned_quibs,
        )
        return self

    def setp(self,
             assigned_name: Union[None, str] = NoValue,
             name: Union[None, str] = NoValue,
             save_directory: Union[None, str, pathlib.Path] = NoValue,
             save_format: Union[None, str, SaveFormat] = NoValue,
             allow_overriding: bool = NoValue,
             assignment_template: Union[None, tuple, AssignmentTemplate] = NoValue,
             caching: Union[str, CachingOptions] = NoValue,
             graphics_update_type: Union[None, str] = NoValue,
             assigned_quibs: Set[Quib] = NoValue,
             ):
        """
        Set one or more properties on a quib.

        Settable properties:
         allow_overriding: bool
         assignment_template: Union[tuple, AssignmentTemplate],
         save_directory: Union[str, pathlib.Path],
         save_format: Union[None, str, SaveFormat],
         caching: Union[str, CachingOptions],
         assigned_name: Union[None, str],
         name: Union[None, str],
         graphics_update_type: Union[None, str]

        Examples:
            >>> a = iquib(7).setp(assigned_name='my_number')
            >>> b = (2 * a).setp(allow_overriding=True)
        """

        from pyquibbler.quib.factory import get_quib_name
        if allow_overriding is not NoValue:
            self.allow_overriding = allow_overriding
        if assignment_template is not NoValue:
            self.set_assignment_template(assignment_template)
        if save_directory is not NoValue:
            self.save_directory = save_directory
        if save_format is not NoValue:
            self.save_format = save_format
        if caching is not NoValue:
            self.caching = caching
        if assigned_name is not NoValue:
            self.assigned_name = assigned_name
        if name is not NoValue:
            self.assigned_name = name
        if graphics_update_type is not NoValue:
            self.graphics_update_type = graphics_update_type
        if assigned_quibs is not NoValue:
            self.assigned_quibs = assigned_quibs

        if assigned_name is NoValue and self.assigned_name is None:
            var_name = get_quib_name()
            if var_name:
                self.assigned_name = var_name

        return self

    @property
    def assignment_template(self) -> AssignmentTemplate:
        """
        Returns an AssignmentTemplate object indicating type and range restricting assignments to the quib.

        See Also
        --------
        assign
        AssignmentTemplate
        """
        return self._assignment_template

    @assignment_template.setter
    @validate_user_input(template=AssignmentTemplate)
    def assignment_template(self, template):
        self._assignment_template = template

    def set_assignment_template(self, *args) -> None:
        """
        Sets an assignment template for the quib.

        The assignment template restricts the values of any future assignments to the quib.

        Options:
        Set a specific AssignmentTemplate object:

        >>> quib.set_assignment_template(assignment_template)

        Set a bound template between `start` and `stop`:

        >>> quib.set_assignment_template(start, stop)

        Set a bound template between `start` and `stop`, with specified `step`

        >>> quib.set_assignment_template(start, stop, step)

        Remove the assignment_template:

        >>> quib.set_assignment_template(None)

        See Also
        --------
        AssignmentTemplate, assignment_template
        """
        self._assignment_template = create_assignment_template(*args)

    @property
    def caching(self):
        """
        The caching mode for the quib.

        Options:
        'auto':     Caching is decided automatically according to the ratio between evaluation time and
                    memory consumption. Quibs with random or graphics functions are always cached.
        'on':       Always cache.
        'off':      Do not cache, unless the quib's function is random or graphics.

        Returns
        -------
        'auto', 'on', or 'off'

        See Also
        --------
        CachingOptions
        cache_status
        """
        return self._caching

    @caching.setter
    @validate_user_input(caching=(str, CachingOptions))
    def caching(self, caching: Union[str, CachingOptions]):
        self._caching = get_enum_by_str(CachingOptions, caching)

    @property
    def graphics_update_type(self) -> Union[None, str]:
        """
        Return the graphics_update_type indicating whether the quib should refresh upon upstream assignments.
        Options are:
        "drag":     refresh immediately as upstream objects are dragged
        "drop":     refresh at end of dragging upon graphic object drop.
        "central":  do not automatically refresh. Refresh, centrally upon refresh_graphics().
        "never":    Never refresh.

        Returns
        -------
        "drag", "drop", "central", "never", or None

        See Also
        --------
        UpdateType, Project.refresh_graphics
        """
        return self._graphics_update_type.value if self._graphics_update_type else None

    @graphics_update_type.setter
    @validate_user_input(graphics_update_type=(type(None), str, UpdateType))
    def graphics_update_type(self, graphics_update_type: Union[None, str, UpdateType]):
        self._graphics_update_type = get_enum_by_str(UpdateType, graphics_update_type, allow_none=True)

    @property
    def allow_overriding(self):
        """
        Indicates whether the quib can be overridden.
        The default for allow_overriding is True for iquibs and False in function quibs.

        Returns
        -------
        bool

        See Also
        --------
        assign, assigned_quibs
        """
        return self._allow_overriding

    @allow_overriding.setter
    @validate_user_input(allow_overriding=bool)
    def allow_overriding(self, allow_overriding: bool):
        self._allow_overriding = allow_overriding

    @property
    def assigned_quibs(self) -> Union[None, Set]:
        """
        Set of quibs to which assignments to this quib could translate to and override.

        When assigned_quibs is None, a dialog will be used to choose between options.

        Returns
        -------
        None or set of Quib

        See Also
        --------
        assign, allow_overriding
        """
        return self._assigned_quibs

    @assigned_quibs.setter
    def assigned_quibs(self, quibs: Optional[Iterable[Quib]]) -> None:
        if quibs is not None:
            try:
                quibs = set(quibs)
                if not all(map(lambda x: isinstance(x, Quib), quibs)):
                    raise Exception
            except Exception:
                raise InvalidArgumentValueException(
                    var_name='assigned_quibs',
                    message='a set of quibs.',
                ) from None

        self._assigned_quibs = quibs

    @property
    def save_format(self):
        """
        Indicates the file format in which quib assignments are saved.

        Options:
            'txt' - save assignments as text file.
            'binary' - save assignments as a binary file.
            'value_txt' - save the quib value as a text file.
            `None` - yield to the Project default save_format

        See Also
        --------
         SaveFormat
        """
        return self._save_format

    @save_format.setter
    @validate_user_input(save_format=(type(None), str, SaveFormat))
    def save_format(self, save_format):
        save_format = get_enum_by_str(SaveFormat, save_format, allow_none=True)
        if self.is_iquib is False and (save_format in [SaveFormat.VALUE_BIN, SaveFormat.VALUE_TXT]):
            raise CannotSaveFunctionQuibsAsValueException()

        self._save_format = save_format
        self._on_file_name_changed()

    @property
    def save_directory(self) -> PathWithHyperLink:
        """
        The directory where quib assignments are saved.

        Can be set to a str or Path object.

        If the directory is absolute, it is used as is.
        If directory is relative, it is used relative to the project directory.
        If directory is None, the project directory is used.

        Returns
        -------
        pathlib.Path

        See Also
        --------
        file_path
        """
        return PathWithHyperLink(self._save_directory) if self._save_directory else None

    @save_directory.setter
    @validate_user_input(directory=(type(None), str, pathlib.Path))
    def save_directory(self, directory: Union[None, str, pathlib.Path]):
        if isinstance(directory, str):
            directory = pathlib.Path(directory)
        self._save_directory = directory
        self._on_file_name_changed()

    @property
    @_verify_quib_connection
    def actual_save_format(self) -> SaveFormat:
        """
        The actual save_format used by the quib.

        The quib's actual_save_format is its save_format if defined.
        Otherwise it defaults to the project's save_format.

        Returns
        -------
        SaveFormat

        See Also
        --------
        save_format
        SaveFormat
        """

        actual_save_format = self.save_format if self.save_format else self._quib.project.save_format
        if self.is_iquib is False:
            actual_save_format = SAVE_FORMAT_TO_FQUIB_SAVE_FORMAT[actual_save_format]
        return actual_save_format

    @property
    @_verify_quib_connection
    def file_path(self) -> Optional[PathWithHyperLink]:
        """
        The full path for the file where quib assignments are saved.
        The path is defined as the [actual_save_directory]/[assigned_name].ext
        ext is determined by the actual_save_format

        Returns
        -------
        pathlib.Path or None

        See Also
        --------
        save_directory, actual_save_directory
        save_format, actual_save_format
        assigned_name
        Project.directory
        """
        return self._get_file_path()

    def _get_file_path(self, response_to_file_not_defined: ResponseToFileNotDefined = ResponseToFileNotDefined.IGNORE) \
            -> Optional[PathWithHyperLink]:

        if self.assigned_name is None or self.actual_save_directory is None or self.actual_save_format is None:
            path = None
            exception = FileNotDefinedException(
                self.assigned_name, self.actual_save_directory, self.actual_save_format)
            if response_to_file_not_defined == ResponseToFileNotDefined.RAISE:
                raise exception
            elif response_to_file_not_defined == ResponseToFileNotDefined.WARN \
                    or response_to_file_not_defined == ResponseToFileNotDefined.WARN_IF_DATA \
                    and self._quib.handler.is_overridden:
                warnings.warn(str(exception))
        else:
            path = PathWithHyperLink(self.actual_save_directory /
                                     (self.assigned_name + SAVE_FORMAT_TO_FILE_EXT[self.actual_save_format]))

        return path

    @property
    @_verify_quib_connection
    def actual_save_directory(self) -> Optional[pathlib.Path]:
        """
        The actual directory where quib file is saved.

        By default, the quib's save_directory is None and the actual_save_directory defaults to the
        project's save_directory.
        Otherwise, if the quib's save_directory is defined as an absolute directory then it is used as is,
        and if it is defined as a relative path it is used relative to the project's directory.

        Returns
        -------
        pathlib.Path

        See Also
        --------
        save_directory
        Project.directory
        SaveFormat
        """
        save_directory = self.save_directory
        if save_directory is not None and save_directory.is_absolute():
            return save_directory  # absolute directory
        elif self._quib.project.directory is None:
            return None
        else:
            return self._quib.project.directory if save_directory is None \
                else self._quib.project.directory / save_directory

    @property
    def assigned_name(self) -> Optional[str]:
        """
        Returns the assigned_name of the quib

        The assigned_name can either be a name automatically created based on the variable name to which the quib
        was first assigned, or a manually assigned name set by setp or by assigning to assigned_name,
        or None indicating unnamed quib.

        The name must be a string starting with a letter and continuing with alpha-numeric charaters. Spaces
        are also allowed.

        The assigned_name is also used for setting the file name for saving overrides.

        Returns
        -------
        str, None

        See Also
        --------
        name, setp, Project.save_quibs, Project.load_quibs
        """
        return self._assigned_name

    @assigned_name.setter
    @validate_user_input(assigned_name=(str, type(None)))
    def assigned_name(self, assigned_name: Optional[str]):
        if assigned_name is None \
                or len(assigned_name) \
                and assigned_name[0].isalpha() and all([c.isalnum() or c in ' _' for c in assigned_name]):
            self._assigned_name = assigned_name
            self._on_file_name_changed()
        else:
            raise ValueError('name must be None or a string starting with a letter '
                             'and continuing alpha-numeric characters or spaces')

    @property
    @_verify_quib_connection
    def name(self) -> Optional[str]:
        """
        Returns the name of the quib

        The name of the quib can either be the given assigned_name if not None,
        or an automated name representing the function of the quib (the functional_representation attribute).

        Assigning into name is equivalent to assigning into assigned_name

        Returns
        -------
        str

        See Also
        --------
        assigned_name, setp, functional_representation
        """
        return self.assigned_name or self.functional_representation

    @name.setter
    @validate_user_input(name=(str, type(None)))
    @_verify_quib_connection
    def name(self, name: Optional[str]):
        self.assigned_name = name

    @property
    @_verify_quib_connection
    def functional_representation(self) -> str:
        """
        Returns a string representing a functional representation of the quib.

        Returns
        -------
        str

        See Also
        --------
        name
        assigned_name
        functional_representation
        pretty_repr
        get_math_expression

        Examples
        --------
        >>> a = iquib(4)
        >>> a.functional_representation
        "iquib(4)"
        """
        return str(self._quib._get_functional_representation_expression())

    @property
    @_verify_quib_connection
    def created_in(self) -> Optional[FileAndLineNumber]:
        """
        The file and line number where the quib was created.

        Returns a FileAndLineNumber object indicating the place where the quib was created.

        None if creation place is unknown.

        Returns
        -------
        FileAndLineNumber or None
        """
        return self._quib.created_in

    @property
    def is_iquib(self) -> Optional[bool]:
        """
        Returns True if the quib is an input quib (iquib).

        Returns
        -------
        bool

        See Also
        --------
        func
        SaveFormat
        """
        return getattr(self._quib.func, '__name__', None) == 'iquib' if self._quib_ref \
            else None

    """
    func_defintion attribuites
    """

    @property
    @_verify_func_definition_connection
    def is_graphics(self):
        """
        Specifies whether the function runs by the quib is a graphics function.

        `True` for known graphics functions
        `False` for known non-graphics functions
        `None` for functions that may create graphics (such as for user functions).

        Returns
        -------
        True, False, or None

        See Also
        --------
        is_graphics_quib, graphics_update_type
        """
        return self._func_definition.is_graphics

    @property
    @_verify_func_definition_connection
    def pass_quibs(self) -> bool:
        return self._func_definition.pass_quibs

    @pass_quibs.setter
    @_verify_func_definition_connection
    @validate_user_input(pass_quibs=bool)
    def pass_quibs(self, pass_quibs):
        self._func_definition.pass_quibs = pass_quibs

    @property
    @_verify_func_definition_connection
    def is_impure(self) -> bool:
        """
        Indicates whether the quib runs an impure function.

        Returns `True` is the function of the quib is impure,
        either random function or file reading.

        See Also
        --------
        is_random, is_file_loading
        Project.reset_impure_quibs

        Returns
        -------
        bool
            Indicating True for impure functions.

        Examples
        --------
        >>> n = iquib(5)
        >>> r = np.random.randint(0, n)
        >>> r.props.is_impure
        True
        """
        return self._func_definition.is_impure

    @property
    @_verify_func_definition_connection
    def is_random(self) -> bool:
        """
        Indicates whether the quib represents a random function.

        A quib that represents a random function automatically caches its value.
        Thereby, repeated calls to the quib return the same random cached results (quenched randomization).
        This behaviour guarentees mathematical consistency (for example, if ``r`` is a random quib ``s = r - r``
        will always have a value of 0).

        The quib can be re-evaluated (randomized), by invalidating its value either locally using `invalidate()`
        or centrally, using `Project.reset_random_quibs()`

        See Also
        --------
        is_impure, is_file_loading
        Quib.invalidate
        Project.reset_random_quibs

        Returns
        -------
        bool
            Indicating True for random functions.

        Examples
        --------
        >>> n = iquib(5)
        >>> r = np.random.randint(0, n)
        >>> r.props.is_random
        True
        """
        return self._func_definition.is_random

    @property
    @_verify_func_definition_connection
    def is_file_loading(self) -> bool:
        """
        Indicates whether the quib represents a function that loads external files.

        A quib whose value depends on the content of external files automatically caches its value.
        Thereby, repeated calls to the quib return the same results even if the file changes.

        The quib can be re-evaluated, by invalidating its value either locally using `invalidate()`
        or centrally, using `Project.reset_file_loading_quibs()`

        See Also
        --------
        is_impure, is_random
        Quib.invalidate
        Project.reset_file_loading_quibs

        Returns
        -------
        bool
            Indicating True for random functions.

        Examples
        --------
        >>> file_name = iquib('my_file.txt')
        >>> x = np.loadtxt(file_name)
        >>> x.props.is_file_loading
        True
        """
        return self._func_definition.is_file_loading

    def __repr__(self):
        repr_ = ''
        repr_ = repr_ + f'{"Settable properties":>26}\n'
        repr_ = repr_ + f'{"-------------------":>26}\n'
        repr_ = repr_ + '\n'.join((f'{prop:>26}: {getattr(self, prop)}' for prop, settable in
                                   self.PROPERTIES_AND_IS_SETTABLE if settable))
        if self._quib:
            repr_ = repr_ + '\n\n'
            repr_ = repr_ + f'{"Derived properties":>26}\n'
            repr_ = repr_ + f'{"------------------":>26}\n'
            repr_ = repr_ + '\n'.join((f'{prop:>26}: {getattr(self, prop)}' for prop, settable in
                                       self.PROPERTIES_AND_IS_SETTABLE if not settable))

        if self._func_definition:
            repr_ = repr_ + '\n\n'
            repr_ = repr_ + f'{"Function definition":>26}\n'
            repr_ = repr_ + f'{"------------------":>26}\n'
            repr_ = repr_ + '\n'.join((f'{prop:>26}: {getattr(self, prop)}' for prop, settable in
                                       self.PROPERTIES_AND_IS_SETTABLE if not settable))
        return repr_
