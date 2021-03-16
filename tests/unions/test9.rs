// Unsafe Union field call as a parameter to a function (as a field of a struct)

fn main() {

	union Sample {
		first: u8,
		second: u8
 	}

 	struct Example {
 		uno: Sample
 	}

	let instantiation = Sample{ first: 23 };

	let new = Example{ uno: instantiation};

	tester(instantiation, new.uno.first);

}

fn tester(a: u8, b: u8) -> u8 {
	return a
}
