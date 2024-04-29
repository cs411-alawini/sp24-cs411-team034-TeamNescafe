'use client';
import { useState, useEffect } from 'react';
import apiService from '@/controllers/apiService';
import { useParams } from 'next/navigation';
import 'react-toastify/dist/ReactToastify.css';
import { ToastContainer, toast } from 'react-toastify';
import Link from 'next/link';
import Image from 'next/image';

const PropertyDetails = () => {
	const params = useParams();
	const { id } = params;
	const [property, setProperty] = useState([]);
	const [review, setReview] = useState([]);
	const [rating, setRating] = useState([]);

	useEffect(() => {
		apiService
			.propertyDetails({ property_id: id })
			.then((propertyDetails) => {
				setProperty(propertyDetails);
			});
	}, []);

	const {
		name,
		address,
		latitude,
		longitude,
		company_name,
		pincode,
		photos,
		avgRating,
		reviews,
		units,
	} = property;

	return (
		<div>
			{' '}
			{!property && <div>Loading</div>}
			{property && photos && (
				<div className='flex flex-col'>
					<div className='min-w-full'>
						<h2 className='mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900'>
							{name}
						</h2>
					</div>
					<div className='flex flex-col gap-2 m-2'>
						<div className='flex gap-2'>
							<div className=''>
								<Image
									src={photos[0]}
									alt={`Property ${name}`}
									width={500}
									height={500}
									className='w-full h-auto rounded-lg shadow-lg'
								/>
							</div>
							<div className='flex w-full flex-col'>
								<table className='w-full border-collapse bg-white rounded-lg shadow-md'>
									<tbody>
										<tr>
											<td className='px-4 py-2 font-semibold'>
												Company Name:
											</td>
											<td className='px-4 py-2'>
												{company_name}
											</td>
										</tr>
										<tr>
											<td className='px-4 py-2 font-semibold'>
												Average Rating:
											</td>
											<td className='px-4 py-2'>
												{avgRating.toFixed(2)}
												/5
											</td>
										</tr>
										<tr>
											<td className='px-4 py-2 font-semibold'>
												Address:
											</td>
											<td className='px-4 py-2'>
												{address}
											</td>
										</tr>
										<tr>
											<td className='px-4 py-2 font-semibold'>
												Pincode:
											</td>
											<td className='px-4 py-2'>
												{pincode}
											</td>
										</tr>
									</tbody>
								</table>

								<div className='w-full border-collapse rounded-lg shadow-md my-4'>
									<h3 className='font-semibold px-4 py-2'>
										Units:
									</h3>
									{units.map((unit, index) => (
										<Link
											key={unit.unit_id}
											href={`/unit/${unit.unit_id}`}
										>
											<p
												className={`${
													index % 2 === 0
														? 'bg-gray-100'
														: 'bg-gray-200'
												} block px-4 py-2 hover:bg-gray-300`}
											>
												{unit.apartment_no}
											</p>
										</Link>
									))}
								</div>
							</div>
						</div>
						<div className='mt-2 w-full'>
							<h3 className='font-semibold mb-2 text-center'>
								Reviews
							</h3>
							{reviews.map((review, index) => (
								<div
									key={index}
									className='w-full border-collapse rounded-lg border-b my-4 '
								>
									<div className='flex justify-between items-center px-2'>
										<p className='font-semibold px-2'>
											{review.user_name}
										</p>
										<p className='px-2'>
											{review.rating}/5
										</p>
									</div>
									<p className='px-4 py-1'>
										{review.comment}
									</p>
									<p className='text-sm text-gray-500 px-4 py-2'>
										{new Date(
											review.created_at
										).toLocaleDateString()}
									</p>
								</div>
							))}

						</div>
					</div>
				</div>
			)}
			<ToastContainer />
		</div>
	);
};

export default PropertyDetails;
